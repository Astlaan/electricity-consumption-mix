import pandas as pd
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import os
import json
from typing import Dict, Any, Optional, List
import aiohttp
import asyncio
import logging
import shutil
from dataclasses import dataclass
import aiofiles
import utils

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Note: All datetimes are assumed to be in UTC, even though they're stored as naive datetimes


@dataclass
class Data:
    generation_pt: pd.DataFrame
    generation_es: pd.DataFrame
    flow_pt_to_es: pd.DataFrame
    flow_es_to_pt: pd.DataFrame


class ENTSOEDataFetcher:
    BASE_URL = "https://web-api.tp.entsoe.eu/api"
    CACHE_DIR = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", ".data_cache"
    )
    STANDARD_GRANULARITY = timedelta(hours=1)  # Set the standard granularity to 1 hour
    CACHE_EXTENSION = "pkl.gz"
    COMPRESSION_METHOD = "gzip"

    def __init__(self):
        self.security_token = os.getenv("ENTSOE_API_KEY")
        if not self.security_token:
            raise ValueError(
                "ENTSOE_API_KEY environment variable is not set. Please set it with your ENTSO-E API key."
            )
        self.is_initialized = {}
        os.makedirs(self.CACHE_DIR, exist_ok=True)

    def get_data(self, start_date: datetime, end_date: datetime, progress_callback=None) -> Data:
        """Fetch all required data for Portugal and Spain in parallel.

        Args:
            start_date: Start of period (inclusive)
            end_date: End of period (exclusive)
            progress_callback: Optional callback function to report progress

        Returns:
            Data object containing all required dataframes
        """

        utils.validate_inputs(start_date, end_date)

        async def _async_get_data():
            return await asyncio.gather(
                self._async_get_generation_data(
                    "10YPT-REN------W", start_date, end_date, progress_callback
                ),  # PT generation
                self._async_get_generation_data(
                    "10YES-REE------0", start_date, end_date, progress_callback
                ),  # ES generation
                self._async_get_physical_flows(
                    "10YES-REE------0", "10YPT-REN------W", start_date, end_date, progress_callback
                ),  # ES->PT flow
                self._async_get_physical_flows(
                    "10YPT-REN------W", "10YES-REE------0", start_date, end_date, progress_callback
                ),  # PT->ES flow
            )

        # Run the async operations
        results = asyncio.run(_async_get_data())

        # Pack results into Data object
        return Data(
            generation_pt=results[0],
            generation_es=results[1],
            flow_es_to_pt=results[2],
            flow_pt_to_es=results[3],
        )

    async def _save_to_cache(
        self, params: Dict[str, Any], data: pd.DataFrame, metadata: Dict[str, Any]
    ):
        cache_name = utils.get_cache_filename(params)
        cache_file = os.path.join(self.CACHE_DIR, f"{cache_name}.{self.CACHE_EXTENSION}")
        logger.debug(f"Attempting to save cache file: {cache_name}")

        # # Save column order in metadata
        # metadata["column_order"] = data.columns.tolist()

        # Use asyncio.to_thread for the pandas operation since it's CPU-bound
        await asyncio.to_thread(data.to_pickle, cache_file, compression={'method': self.COMPRESSION_METHOD, 'compresslevel': 1, "mtime": 0})

        metadata_file = os.path.join(self.CACHE_DIR, f"{cache_name}_metadata.json")
        async with aiofiles.open(metadata_file, "w") as f:
            await f.write(json.dumps(metadata))
        logger.debug("Successfully saved cache files")

    async def _load_from_cache(self, params: Dict[str, Any]) -> Optional[tuple]:
        cache_name = utils.get_cache_filename(params)
        cache_file = os.path.join(self.CACHE_DIR, f"{cache_name}.{self.CACHE_EXTENSION}")
        metadata_file = os.path.join(self.CACHE_DIR, f"{cache_name}_metadata.json")

        if os.path.exists(cache_file) and os.path.exists(metadata_file):
            # Use asyncio.to_thread for the pandas operation since it's CPU-bound
            try:
                async with aiofiles.open(metadata_file, "r") as f:
                    metadata = json.loads(await f.read())

                data = await asyncio.to_thread(pd.read_pickle, cache_file)

                # # Restore column order from metadata if available
                # if "column_order" in metadata:
                #     data = data[metadata["column_order"]]

                # Convert string representation back to Timedelta if necessary
                if "resolution" in metadata and isinstance(metadata["resolution"], str):
                    metadata["resolution"] = pd.Timedelta(metadata["resolution"])

                # Convert cached dates to naive datetime objects
                metadata["start_date_inclusive"] = pd.to_datetime(
                    metadata["start_date_inclusive"]
                ).tz_localize(None)
                metadata["end_date_exclusive"] = pd.to_datetime(
                    metadata["end_date_exclusive"]
                ).tz_localize(None)

                return data, metadata
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from cache: {str(e)}")
                # Remove the corrupted cache files
                os.remove(cache_file)
                os.remove(metadata_file)
                return None
        return None

    async def _get_latest_cache_date(
        self, params: Dict[str, Any]
    ) -> Optional[datetime]:
        cached_data = await self._load_from_cache(params)
        if cached_data is not None:
            df, metadata = cached_data
            if not df.empty and "start_time" in df.columns:
                return df["start_time"].max()
        return None

    async def _async_parse_xml_to_dataframe(self, xml_data: str) -> pd.DataFrame:
        """Async wrapper for XML parsing"""
        df = await asyncio.to_thread(self._parse_xml_internal, xml_data)
        df = utils.resample_to_standard_granularity(df, self.STANDARD_GRANULARITY)
        return df
    

    def _parse_xml_internal(self, xml_data: str) -> pd.DataFrame:
        """Synchronous XML parsing function to run in thread pool"""
        root = ET.fromstring(xml_data)
        namespace = {"ns": root.tag.split("}")[0].strip("{")}

        data = []
        document_type = root.find(".//ns:type", namespace)
        is_flow_data = document_type is not None and document_type.text == "A11"

        # XPath expressions 
        time_series_path = ".//ns:TimeSeries"
        psr_type_path = ".//ns:psrType"
        period_path = ".//ns:Period"
        start_path = ".//ns:start"
        resolution_path = ".//ns:resolution"
        point_path = ".//ns:Point"
        position_path = "ns:position"
        quantity_path = "ns:quantity"

        for time_series in root.findall(time_series_path, namespace):
            if not is_flow_data and time_series.find(".//ns:outBiddingZone_Domain.mRID", namespace) is not None:
                continue
    
            psr_type = None
            if not is_flow_data:
                psr_type_elem = time_series.find(psr_type_path, namespace)
                psr_type = (
                    psr_type_elem.text if psr_type_elem is not None else "Unknown"
                )

            period = time_series.find(period_path, namespace)
            if period is None:
                continue

            start_time = period.find(start_path, namespace)
            resolution = period.find(resolution_path, namespace)

            if start_time is None or resolution is None:
                continue

            start_time = pd.to_datetime(start_time.text).tz_localize(None)
            resolution = pd.Timedelta(resolution.text)

            for point in period.findall(point_path, namespace):
                position = point.find(position_path, namespace)
                quantity = point.find(quantity_path, namespace)

                if position is None or quantity is None:
                    continue

                point_start_time = start_time + resolution * (int(position.text) - 1)
                # point_end_time = point_start_time + resolution

                data_point = {
                    "start_time": point_start_time,
                    # "end_time": point_end_time,
                    # "resolution": resolution,
                }

                # Use 'Power' column name for flow data, otherwise use quantity with psr_type
                if is_flow_data:
                    data_point["Power"] = float(quantity.text)
                else:
                    data_point["quantity"] = float(quantity.text)
                    data_point["psr_type"] = psr_type

                data.append(data_point)

        if not data:
            columns = ["start_time"]
            if is_flow_data:
                columns.append("Power")
            else:
                columns.extend(["quantity", "psr_type"])
            return pd.DataFrame(columns=columns)

        df = pd.DataFrame(data)

        # Pivot the DataFrame if it's generation data
        if not df.empty and "psr_type" in df.columns:
            # TODO: Fails without this duplicate finding, figure out why
            # First aggregate any duplicate entries by taking the mean
            df = (
                df.groupby(["start_time", "psr_type"])[
                    "quantity"
                ]
                .mean()
                .reset_index()
            )

            # Then pivot
            df = df.pivot(
                index="start_time",
                columns="psr_type",
                values="quantity",
            ).reset_index()
            # df = df.fillna(0) # TODO: is this fine?

            # Remove column name from the pivot operation
            df.columns.name = None
            
        return df

    async def _make_request_async(
        self, session: aiohttp.ClientSession, params: Dict[str, Any]
    ) -> str:
        logger.debug(f"[_make_request_async]: {params}")
        params["securityToken"] = self.security_token

        async with session.get(self.BASE_URL, params=params) as response:
            response.raise_for_status()
            return await response.text()

    async def _fetch_data_in_chunks(
        self, params: Dict[str, Any], start_date: datetime, end_date: datetime
    ) -> List[str]:
        latest_cache_date = await self._get_latest_cache_date(params)
        if latest_cache_date is not None:
            start_date = max(start_date, latest_cache_date)

        tasks = []
        async with aiohttp.ClientSession() as session:
            while start_date < end_date:
                # Ranges of 360 days to avoid the limit with more tolerance
                chunk_end_date = min(start_date + timedelta(days=360), end_date)
                chunk_params = params.copy()
                chunk_params["periodStart"] = start_date.strftime("%Y%m%d%H%M")
                chunk_params["periodEnd"] = chunk_end_date.strftime("%Y%m%d%H%M")
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

        cached_data = await self._load_from_cache(params)

        logger.debug(f"Requested date range: {start_date} to {end_date}")

        fetch_start = start_date
        fetch_end = end_date

        if cached_data is not None: # FULL OR PARTIAL HIT
            df, metadata = cached_data
            cached_start = pd.to_datetime(metadata["start_date_inclusive"])
            cached_end = pd.to_datetime(metadata["end_date_exclusive"])

            # Note: end_date is exclusive, so cached_end should be >= end_date
            # FULL HIT
            if cached_start <= start_date and cached_end >= end_date:
                logger.debug(
                    f"[_fetch_and_cache_data]: FULL CACHE HIT\n{params}\nstart: {start_date}\nend: {end_date}"
                )
                # Note: end_time < end_date because end_date is exclusive
                return df[
                    (df["start_time"] >= start_date) & (df["start_time"] < end_date)
                ]

            # CACHE EXISTS, BUT IT'S A PARTIAL HIT OR FULL MISS
            fetch_start = cached_end
            logger.debug(
                f"[_fetch_and_cache_data]: FETCH NEEDED: \n{params}\ncache_end: {cached_end}\nstart: {start_date}\nend: {end_date}"
            )
            logger.debug(f"Adjusted fetch_start to {fetch_start}")
        else:
            logger.debug(
                f"[_fetch_and_cache_data]: CACHE MISS\n{params}\nstart: {start_date}\nend: {end_date}"
            )

        # Fetch new data
        xml_chunks = await self._fetch_data_in_chunks(params, fetch_start, fetch_end)
        new_df_chunks = await asyncio.gather(
            *[self._async_parse_xml_to_dataframe(xml) for xml in xml_chunks]
        )
        new_df = pd.concat(new_df_chunks, ignore_index=True)

        if cached_data is not None:
            df = pd.concat([cached_data[0], new_df]).drop_duplicates(
                subset=["start_time"], keep="last"
            ).reset_index(drop=True)
        else:
            df = new_df

        if not df.empty:
            metadata = {
                "start_date_inclusive": df["start_time"].min().isoformat(),
                "end_date_exclusive": (df["start_time"].max() + self.STANDARD_GRANULARITY).isoformat(),
            }
            metadata.update(params)
            await self._save_to_cache(params, df, metadata)
            logger.debug(f"Saved to cache: {metadata}")

        return df[(df["start_time"] >= start_date) & (df["start_time"] < end_date)]

    async def _async_get_generation_data(
        self, country_code: str, start_date: datetime, end_date: datetime, progress_callback=None
    ) -> pd.DataFrame:
        params = {
            "documentType": "A75",
            "processType": "A16",
            "in_Domain": country_code,
            "outBiddingZone_Domain": country_code,
        }

        df = await self._fetch_and_cache_data(params, start_date, end_date)
        if progress_callback:
            progress_callback()
        return df

    async def _async_get_physical_flows(
        self, out_domain: str, in_domain: str, start_date: datetime, end_date: datetime, progress_callback=None
    ) -> pd.DataFrame:
        params = {
            "documentType": "A11",
            "in_Domain": in_domain,
            "out_Domain": out_domain,
        }

        df = await self._fetch_and_cache_data(params, start_date, end_date)
        if progress_callback:
            progress_callback()
        return df

    def reset_cache(self):
        """Delete all cached data."""
        if os.path.exists(self.CACHE_DIR):
            print(f"Deleting cache directory: {self.CACHE_DIR}")
            shutil.rmtree(self.CACHE_DIR)
            os.makedirs(self.CACHE_DIR)  # Recreate empty cache dir

    ########## For testing ###########

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

    def _get_generation_data(
        self, country_code: str, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Get generation data for a country in a given time range.

        Args:
            country_code: The country code
            start_date: Start of period (inclusive)
            end_date: End of period (exclusive)
        """
        loop = asyncio.get_event_loop()
        generation = loop.run_until_complete(
            self._async_get_generation_data(country_code, start_date, end_date)
        )
        return generation

    # def check_data_gaps(self, df: pd.DataFrame, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    #     """Check for gaps in time series data.

    #     Args:
    #         df: DataFrame with time series data
    #         start_date: Start of period to check (inclusive)
    #         end_date: End of period to check (exclusive)

    #     Returns:
    #         Dict containing:
    #             has_gaps (bool): Whether gaps were found
    #             gap_periods (List[Dict]): List of gap periods with start/end times
    #             total_gaps (int): Number of missing intervals
    #             coverage_percentage (float): Percentage of intervals with data
    #     """
    #     if df.empty:
    #         return {
    #             'has_gaps': True,
    #             'gap_periods': [{
    #                 'start': start_date,
    #                 'end': end_date,
    #                 'duration': end_date - start_date
    #             }],
    #             'total_gaps': int((end_date - start_date) / self.STANDARD_GRANULARITY),
    #             'coverage_percentage': 0.0
    #         }

    #     # Create a complete time index at standard granularity
    #     # Note: end_date - 1 second to exclude the end_date itself since it's exclusive
    #     expected_index = pd.date_range(
    #         start=start_date,
    #         end=end_date - timedelta(seconds=1),
    #         freq=self.STANDARD_GRANULARITY
    #     )

    #     # Get unique timestamps from the data
    #     actual_times = pd.DatetimeIndex(df['start_time'].unique())

    #     # Find missing timestamps
    #     missing_times = expected_index.difference(actual_times)

    #     # Group consecutive missing timestamps into periods
    #     gap_periods = []
    #     if len(missing_times) > 0:
    #         gap_start = missing_times[0]
    #         prev_time = gap_start

    #         for time in missing_times[1:]:
    #             if time - prev_time > self.STANDARD_GRANULARITY:
    #                 # Gap ends, record it
    #                 gap_periods.append({
    #                     'start': gap_start,
    #                     'end': prev_time + self.STANDARD_GRANULARITY,
    #                     'duration': prev_time + self.STANDARD_GRANULARITY - gap_start
    #                 })
    #                 gap_start = time
    #             prev_time = time

    #         # Add final gap period
    #         gap_periods.append({
    #             'start': gap_start,
    #             'end': prev_time + self.STANDARD_GRANULARITY,
    #             'duration': prev_time + self.STANDARD_GRANULARITY - gap_start
    #         })

    #     expected_intervals = len(expected_index)
    #     actual_intervals = len(actual_times)

    #     return {
    #         'has_gaps': len(missing_times) > 0,
    #         'gap_periods': gap_periods,
    #         'total_gaps': len(missing_times),
    #         'coverage_percentage': (actual_intervals / expected_intervals) * 100 if expected_intervals > 0 else 0.0,
    #         'missing_times': missing_times.tolist()  # For detailed analysis if needed
    #     }
