import requests
import pandas as pd
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import os
import json
import hashlib
from typing import Dict, Any, Optional, List
import aiohttp
import asyncio
import logging
import shutil
from dataclasses import dataclass

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Note: All datetimes are assumed to be in UTC, even though they're stored as naive datetimes


@dataclass
class Data:
    generation_pt: pd.DataFrame
    generation_es: pd.DataFrame
    flow_es_to_pt: pd.DataFrame
    flow_pt_to_es: pd.DataFrame


class ENTSOEDataFetcher:
    BASE_URL = "https://web-api.tp.entsoe.eu/api"
    CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".data_cache")
    STANDARD_GRANULARITY = timedelta(hours=1)  # Set the standard granularity to 1 hour

    def __init__(self):
        self.security_token = os.getenv('ENTSOE_API_KEY')
        if not self.security_token:
            raise ValueError("ENTSOE_API_KEY environment variable is not set. Please set it with your ENTSO-E API key.")
        self.is_initialized = {}
        os.makedirs(self.CACHE_DIR, exist_ok=True)

    def _get_cache_filename(self, params: Dict[str, Any]) -> str:
        """Generate cache filename based on data type and countries."""
        document_type = params.get('documentType')
        in_domain = params.get('in_Domain', '')
        out_domain = params.get('out_Domain', '')

        if document_type == 'A75':  # Generation data
            if 'PT' in in_domain:
                return "generation_pt"
            elif 'ES' in in_domain:
                return "generation_es"
        elif document_type == 'A11':  # Flow data
            if 'PT' in out_domain and 'ES' in in_domain:
                return "flow_pt_to_es"
            elif 'ES' in out_domain and 'PT' in in_domain:
                return "flow_es_to_pt"
        
        raise ValueError(f"Unsupported combination of document type and domains")

    def _save_to_cache(self, params: Dict[str, Any], data: pd.DataFrame, metadata: Dict[str, Any]):
        cache_name = self._get_cache_filename(params)
        cache_file = os.path.join(self.CACHE_DIR, f"{cache_name}.parquet")
        print(f"Attempting to save cache file: {cache_file}")
        data.to_parquet(cache_file)
        
        if 'resolution' in metadata and isinstance(metadata['resolution'], pd.Timedelta):
            metadata['resolution'] = str(metadata['resolution'])

        metadata_file = os.path.join(self.CACHE_DIR, f"{cache_name}_metadata.json")
        logger.debug(f"Attempting to save metadata file: {metadata_file}")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        logger.debug("Successfully saved cache files")

    def _load_from_cache(self, params: Dict[str, Any]) -> Optional[tuple]:
        cache_name = self._get_cache_filename(params)
        cache_file = os.path.join(self.CACHE_DIR, f"{cache_name}.parquet")
        metadata_file = os.path.join(self.CACHE_DIR, f"{cache_name}_metadata.json")
        if os.path.exists(cache_file) and os.path.exists(metadata_file):
            data = pd.read_parquet(cache_file)
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)

                # Convert string representation back to Timedelta if necessary
                if 'resolution' in metadata and isinstance(metadata['resolution'], str):
                    metadata['resolution'] = pd.Timedelta(metadata['resolution'])

                # Convert cached dates to naive datetime objects
                metadata['start_date_inclusive'] = pd.to_datetime(metadata['start_date_inclusive']).tz_localize(None)
                metadata['end_date_exclusive'] = pd.to_datetime(metadata['end_date_exclusive']).tz_localize(None)

                return data, metadata
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from cache: {str(e)}")
                # Remove the corrupted cache files
                os.remove(cache_file)
                os.remove(metadata_file)
                return None
        return None

    def _get_latest_cache_date(self, params: Dict[str, Any]) -> Optional[datetime]:
        cached_data = self._load_from_cache(params)
        if cached_data is not None:
            df, metadata = cached_data
            if not df.empty and 'start_time' in df.columns:
                return df['start_time'].max()
        return None

    def _parse_xml_to_dataframe(self, xml_data: str) -> pd.DataFrame:
        logger.debug(f"Raw XML (first 500 chars): {xml_data[:500]}")
        root = ET.fromstring(xml_data)
        namespace = {'ns': root.tag.split('}')[0].strip('{')}

        data = []
        # Corrected line to find 'type' instead of 'documentType'
        document_type = root.find(".//ns:type", namespace)
        is_flow_data = document_type is not None and document_type.text == 'A11'

        logger.debug(f"Document type: {document_type.text if document_type is not None else 'None'}")
        logger.debug(f"Is flow data: {is_flow_data}")

        for time_series in root.findall(".//ns:TimeSeries", namespace):
            psr_type = None
            if not is_flow_data:
                psr_type_elem = time_series.find(".//ns:psrType", namespace)
                psr_type = psr_type_elem.text if psr_type_elem is not None else "Unknown"

            period = time_series.find(".//ns:Period", namespace)
            if period is None:
                continue

            start_time = period.find(".//ns:start", namespace)
            resolution = period.find(".//ns:resolution", namespace)

            if start_time is None or resolution is None:
                continue

            start_time = pd.to_datetime(start_time.text).tz_localize(None)
            resolution = pd.Timedelta(resolution.text)

            for point in period.findall(".//ns:Point", namespace):
                position = point.find("ns:position", namespace)
                quantity = point.find("ns:quantity", namespace)

                if position is None or quantity is None:
                    continue

                point_start_time = start_time + resolution * (int(position.text) - 1)
                point_end_time = point_start_time + resolution

                data_point = {
                    'start_time': point_start_time,
                    'end_time': point_end_time,
                    'resolution': resolution
                }

                # Use 'Power' column name for flow data, otherwise use quantity with psr_type
                if is_flow_data:
                    data_point['Power'] = float(quantity.text)
                else:
                    data_point['quantity'] = float(quantity.text)
                    data_point['psr_type'] = psr_type

                data.append(data_point)

        logger.debug(f"Data points: {data[:2]}")  # Show first two data points
        logger.debug(f"Columns in data: {list(data[0].keys()) if data else 'No data'}")

        if not data:
            columns = ['start_time', 'end_time', 'resolution']
            if is_flow_data:
                columns.append('Power')
            else:
                columns.extend(['quantity', 'psr_type'])
            return pd.DataFrame(columns=columns)

        df = pd.DataFrame(data)

        logger.debug(f"DataFrame columns: {df.columns.tolist()}")

        # Pivot the DataFrame if it's generation data
        if not df.empty and 'psr_type' in df.columns:
            # First aggregate any duplicate entries by taking the mean
            df = df.groupby(['start_time', 'end_time', 'resolution', 'psr_type'])['quantity'].mean().reset_index()
            
            # Then pivot
            df = df.pivot(
                index=['start_time', 'end_time', 'resolution'],
                columns='psr_type',
                values='quantity'
            ).reset_index()
            df = df.fillna(0) # TODO check if this is a good idea

            # Debug print statements
            print("Column structure:", df.columns)
            print("Column names:", list(df.columns.names))

            # Remove psrType as the name of the column's index
            df.columns.name = None
        return df



    async def _make_request_async(self, session: aiohttp.ClientSession, params: Dict[str, Any]) -> str:
        logger.debug(f"[_make_request_async]: {params}")
        params['securityToken'] = self.security_token

        async with session.get(self.BASE_URL, params=params) as response:
            response.raise_for_status()
            return await response.text()

    def _make_request(self, params: Dict[str, Any]) -> str:
        async def run_async():
            async with aiohttp.ClientSession() as session:
                return await self._make_request_async(session, params)

        # Get or create an event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Run the coroutine and return its result
        return loop.run_until_complete(run_async())

    async def _fetch_data_in_chunks(self, params: Dict[str, Any], start_date: datetime, end_date: datetime) -> List[str]:
        latest_cache_date = self._get_latest_cache_date(params)
        if latest_cache_date is not None:
            start_date = max(start_date, latest_cache_date)

        tasks = []
        async with aiohttp.ClientSession() as session:
            while start_date < end_date:
                chunk_end_date = min(start_date + timedelta(days=365), end_date)
                chunk_params = params.copy()
                chunk_params['periodStart'] = start_date.strftime('%Y%m%d%H%M')
                chunk_params['periodEnd'] = chunk_end_date.strftime('%Y%m%d%H%M')
                tasks.append(self._make_request_async(session, chunk_params))
                start_date = chunk_end_date
            return await asyncio.gather(*tasks)

    async def _fetch_and_cache_data(
        self,
        params: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
    ) -> pd.DataFrame:
        if start_date >= end_date:
            raise ValueError("end_date must be greater than start_date")
        """
        Common logic for fetching and caching data from ENTSO-E API.

        Args:
            params: API request parameters
            start_date: Start of requested period (inclusive)
            end_date: End of requested period (exclusive)
        Returns:
            DataFrame with requested data
        """

        cached_data = self._load_from_cache(params)

        logger.debug(f"Requested date range: {start_date} to {end_date}")

        if cached_data is not None:
            df, metadata = cached_data
            cached_start = pd.to_datetime(metadata['start_date_inclusive'])
            cached_end = pd.to_datetime(metadata['end_date_exclusive'])

            # Note: end_date is exclusive, so cached_end should be >= end_date
            if cached_start <= start_date and cached_end >= end_date:
                logger.debug(f"[_fetch_and_cache_data]: FULL CACHE HIT\n{params}\nstart: {start_date}\nend: {end_date}")
                # Note: end_time < end_date because end_date is exclusive
                return df[(df['start_time'] >= start_date) & (df['start_time'] < end_date)]

            # If there's overlap, adjust the request range
            if cached_end > start_date:
                logger.debug(f"[_fetch_and_cache_data]: PARTIAL CACHE HIT\n{params}\ncache_end: {cached_end}\nstart: {start_date}\nend: {end_date}")
                start_date = cached_end
                logger.debug(f"Adjusted start_date to {start_date}")
        else:
            logger.debug(f"[_fetch_and_cache_data]: CACHE MISS\n{params}\nstart: {start_date}\nend: {end_date}")
            is_testing = os.getenv('ENTSOE_TESTING', '').lower() == 'true'

            # if not is_testing:
            #     if tuple(params.items()) in self.is_initialized:
            #         raise ValueError(f"ERROR: Database attempted a 2nd initialization!\n params: {params}")
            #     start_date = datetime(2010, 1, 1, 0, 0)
            #     logger.info("Initializing database with historical data since 2010...")
            #     self.is_initialized[tuple(params.items())] = True


        # Fetch new data
        logger.debug("Fetching new data")
        xml_chunks = await self._fetch_data_in_chunks(params, start_date, end_date)
        new_df = pd.concat([self._parse_xml_to_dataframe(xml) for xml in xml_chunks], ignore_index=True)

        if cached_data is not None:
            df = pd.concat([cached_data[0], new_df]).drop_duplicates(subset=['start_time'], keep='last')
        else:
            df = new_df

        if not df.empty:
            metadata = {
                'start_date_inclusive': df['start_time'].min().isoformat(),
                'end_date_exclusive': df['end_time'].max().isoformat(),
            }
            metadata.update(params)
            self._save_to_cache(params, df, metadata)
            logger.debug(f"Saved to cache: {metadata}")

        return df[(df['start_time'] >= start_date) & (df['start_time'] < end_date)]

    async def get_generation_data_async(self, country_code: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        params = {
            'documentType': 'A75',
            'processType': 'A16',
            'in_Domain': country_code,
            'outBiddingZone_Domain': country_code,
        }

        df = await self._fetch_and_cache_data(params, start_date, end_date)
        result = self._resample_to_standard_granularity(df)
        # logger.debug(f"Returning result with shape: {result.shape}")
        return result

    def get_generation_data(self, country_code: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get generation data for a country in a given time range.

        Args:
            country_code: The country code
            start_date: Start of period (inclusive)
            end_date: End of period (exclusive)
        """
        loop = asyncio.get_event_loop()
        generation = loop.run_until_complete(self.get_generation_data_async(country_code, start_date, end_date))
        return generation

    async def get_physical_flows_async(self, in_domain: str, out_domain: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        params = {
            'documentType': 'A11',
            'in_Domain': in_domain,
            'out_Domain': out_domain,
        }

        df = await self._fetch_and_cache_data(params, start_date, end_date)
        return self._resample_to_standard_granularity(df)

    async def get_data(self, start_date: datetime, end_date: datetime) -> Data:
        """Fetch all required data for Portugal and Spain in parallel.

        Args:
            start_date: Start of period (inclusive)
            end_date: End of period (exclusive)

        Returns:
            Data object containing all required dataframes
        """
        # Create all tasks
        tasks = [
            self.get_generation_data_async('10YPT-REN------W', start_date, end_date),  # PT generation
            self.get_generation_data_async('10YES-REE------0', start_date, end_date),   # ES generation
            self.get_physical_flows_async('10YES-REE------0', '10YPT-REN------W', start_date, end_date),  # ES->PT flow
            self.get_physical_flows_async('10YPT-REN------W', '10YES-REE------0', start_date, end_date)   # PT->ES flow
        ]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks)
        
        # Pack results into Data object
        return Data(
            generation_pt=results[0],
            generation_es=results[1],
            flow_es_to_pt=results[2],
            flow_pt_to_es=results[3]
        )

    def _resample_to_standard_granularity(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df

        # Set start_time as index for resampling
        df = df.set_index('start_time')

        # Get all numeric columns for resampling
        # This will include B01, B02, etc. columns after pivoting
        value_columns = df.select_dtypes(include=['float64', 'int64']).columns

        # Resample each value column
        resampled = df[value_columns].resample(
            self.STANDARD_GRANULARITY,
            offset='0H',  # Start periods at 00 minutes
            label='left',  # Use the start of the period as the label
            closed='left'  # Include the left boundary of the interval
        ).mean()

        # Reset index to get start_time as a column
        resampled = resampled.reset_index()
        
        # Add end_time and resolution columns
        resampled['end_time'] = resampled['start_time'] + self.STANDARD_GRANULARITY
        resampled['resolution'] = self.STANDARD_GRANULARITY

        return resampled

    def check_data_gaps(self, df: pd.DataFrame, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Check for gaps in time series data.

        Args:
            df: DataFrame with time series data
            start_date: Start of period to check (inclusive)
            end_date: End of period to check (exclusive)

        Returns:
            Dict containing:
                has_gaps (bool): Whether gaps were found
                gap_periods (List[Dict]): List of gap periods with start/end times
                total_gaps (int): Number of missing intervals
                coverage_percentage (float): Percentage of intervals with data
        """
        if df.empty:
            return {
                'has_gaps': True,
                'gap_periods': [{
                    'start': start_date,
                    'end': end_date,
                    'duration': end_date - start_date
                }],
                'total_gaps': int((end_date - start_date) / self.STANDARD_GRANULARITY),
                'coverage_percentage': 0.0
            }

        # Create a complete time index at standard granularity
        # Note: end_date - 1 second to exclude the end_date itself since it's exclusive
        expected_index = pd.date_range(
            start=start_date,
            end=end_date - timedelta(seconds=1),
            freq=self.STANDARD_GRANULARITY
        )

        # Get unique timestamps from the data
        actual_times = pd.DatetimeIndex(df['start_time'].unique())

        # Find missing timestamps
        missing_times = expected_index.difference(actual_times)

        # Group consecutive missing timestamps into periods
        gap_periods = []
        if len(missing_times) > 0:
            gap_start = missing_times[0]
            prev_time = gap_start

            for time in missing_times[1:]:
                if time - prev_time > self.STANDARD_GRANULARITY:
                    # Gap ends, record it
                    gap_periods.append({
                        'start': gap_start,
                        'end': prev_time + self.STANDARD_GRANULARITY,
                        'duration': prev_time + self.STANDARD_GRANULARITY - gap_start
                    })
                    gap_start = time
                prev_time = time

            # Add final gap period
            gap_periods.append({
                'start': gap_start,
                'end': prev_time + self.STANDARD_GRANULARITY,
                'duration': prev_time + self.STANDARD_GRANULARITY - gap_start
            })

        expected_intervals = len(expected_index)
        actual_intervals = len(actual_times)

        return {
            'has_gaps': len(missing_times) > 0,
            'gap_periods': gap_periods,
            'total_gaps': len(missing_times),
            'coverage_percentage': (actual_intervals / expected_intervals) * 100 if expected_intervals > 0 else 0.0,
            'missing_times': missing_times.tolist()  # For detailed analysis if needed
        }

    def reset_cache(self):
        """Delete all cached data."""
        if os.path.exists(self.CACHE_DIR):
            print(f"Deleting cache directory: {self.CACHE_DIR}")
            shutil.rmtree(self.CACHE_DIR)
            os.makedirs(self.CACHE_DIR)  # Recreate empty cache dir

