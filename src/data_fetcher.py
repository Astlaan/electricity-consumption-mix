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

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Note: All datetimes are assumed to be in UTC, even though they're stored as naive datetimes


class ENTSOEDataFetcher:
    BASE_URL = "https://web-api.tp.entsoe.eu/api"
    CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".data_cache")
    STANDARD_GRANULARITY = timedelta(hours=1)  # Set the standard granularity to 1 hour
    
    def __init__(self, security_token: str):
        self.security_token = security_token
        os.makedirs(self.CACHE_DIR, exist_ok=True)

    def _ensure_naive_datetime(self, dt):
        if dt is not None:
            return pd.to_datetime(dt).tz_localize(None)
        return dt

    def _get_cache_key(self, params: Dict[str, Any]) -> str:
        param_str = json.dumps(params, sort_keys=True)
        cache_key = hashlib.md5(param_str.encode()).hexdigest()
        return cache_key

    def _save_to_cache(self, cache_key: str, data: pd.DataFrame, metadata: Dict[str, Any]):
        for col in data.select_dtypes(include=['datetime64']).columns:
            data[col] = data[col].apply(self._ensure_naive_datetime)
        
        cache_file = os.path.join(self.CACHE_DIR, f"{cache_key}.parquet")
        data.to_parquet(cache_file)
        
        if 'resolution' in metadata and isinstance(metadata['resolution'], pd.Timedelta):
            metadata['resolution'] = str(metadata['resolution'])
        
        metadata_file = os.path.join(self.CACHE_DIR, f"{cache_key}_metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)

    def _load_from_cache(self, cache_key: str) -> Optional[tuple]:
        cache_file = os.path.join(self.CACHE_DIR, f"{cache_key}.parquet")
        metadata_file = os.path.join(self.CACHE_DIR, f"{cache_key}_metadata.json")
        if os.path.exists(cache_file) and os.path.exists(metadata_file):
            data = pd.read_parquet(cache_file)
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Convert string representation back to Timedelta if necessary
                if 'resolution' in metadata and isinstance(metadata['resolution'], str):
                    metadata['resolution'] = pd.Timedelta(metadata['resolution'])
                
                return data, metadata
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from cache: {str(e)}")
                # Remove the corrupted cache files
                os.remove(cache_file)
                os.remove(metadata_file)
                return None
        return None

    def _get_latest_cache_date(self, params: Dict[str, Any]) -> Optional[datetime]:
        cache_key = self._get_cache_key(params)
        cached_data = self._load_from_cache(cache_key)
        if cached_data is not None:
            df, metadata = cached_data
            if not df.empty and 'start_time' in df.columns:
                return df['start_time'].max()
        return None

    def _get_latest_cache_date(self, params: Dict[str, Any]) -> Optional[datetime]:
        cache_key = self._get_cache_key(params)
        cached_data = self._load_from_cache(cache_key)
        if cached_data is not None:
            df, metadata = cached_data
            if not df.empty and 'start_time' in df.columns:
                return df['start_time'].max()
        return None

    def _make_request(self, params: Dict[str, Any]) -> str:
        params['securityToken'] = self.security_token
        print(f"Making API request with params: {params}")
        try:
            response = requests.get(self.BASE_URL, params=params)
            print(f"API response status code: {response.status_code}")
            # if response.status_code != 200:
            #     print(f"API error response: {response.text}")
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Request failed: {str(e)}")
            raise

    def _parse_xml_to_dataframe(self, xml_data: str) -> pd.DataFrame:
        if not xml_data or "<GL_MarketDocument" not in xml_data:
            logger.warning("Empty or invalid XML data received")
            return pd.DataFrame(columns=['start_time', 'end_time', 'psr_type', 'quantity', 'resolution'])

        root = ET.fromstring(xml_data)
        namespace = {'ns': root.tag.split('}')[0].strip('{')}
        
        data = []
        for time_series in root.findall(".//ns:TimeSeries", namespace):
            psr_type = time_series.find(".//ns:psrType", namespace)
            psr_type = psr_type.text if psr_type is not None else "Unknown"
            
            in_domain = time_series.find(".//ns:in_Domain.mRID", namespace)
            out_domain = time_series.find(".//ns:out_Domain.mRID", namespace)
            
            period = time_series.find(".//ns:Period", namespace)
            if period is None:
                continue
            
            start_time = period.find(".//ns:start", namespace)
            resolution = period.find(".//ns:resolution", namespace)
            
            if start_time is None or resolution is None:
                continue
            
            start_time = self._ensure_naive_datetime(start_time.text)
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
                    'psr_type': psr_type,
                    'quantity': float(quantity.text),
                    'resolution': resolution
                }
                
                if in_domain is not None:
                    data_point['in_domain'] = in_domain.text
                if out_domain is not None:
                    data_point['out_domain'] = out_domain.text
                
                data.append(data_point)
        
        if not data:
            return pd.DataFrame(columns=['start_time', 'end_time', 'psr_type', 'quantity', 'resolution', 'in_domain', 'out_domain'])
        
        df = pd.DataFrame(data)
        df['start_time'] = pd.to_datetime(df['start_time'])
        df['end_time'] = pd.to_datetime(df['end_time'])
        return df

    def get_generation_data(self, country_code: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        params = {
            'documentType': 'A75',
            'processType': 'A16',
            'in_Domain': country_code,
            'outBiddingZone_Domain': country_code,
        }
        cache_key = self._get_cache_key(params)
        start_date = self._ensure_naive_datetime(start_date)
        end_date = self._ensure_naive_datetime(end_date)

        cached_data = self._load_from_cache(cache_key)
        
        logger.debug(f"Requested date range: {start_date} to {end_date}")
        
        if cached_data is not None:
            df, metadata = cached_data
            cached_start = pd.to_datetime(metadata['start_date'])
            cached_end = pd.to_datetime(metadata['end_date'])
            
            logger.debug(f"Cached data range: {cached_start} to {cached_end}")
            
            if cached_start <= start_date and cached_end >= end_date:
                logger.debug("Using cached data")
                return df[(df['start_time'] >= start_date) & (df['start_time'] < end_date)]
            
            # If there's partial overlap, adjust the request range
            if cached_end > start_date:
                start_date = cached_end
                logger.debug(f"Adjusted start_date to {start_date}")
            if cached_start < end_date:
                end_date = cached_start
                logger.debug(f"Adjusted end_date to {end_date}")

        # If we need to fetch new data
        if cached_data is None or start_date < end_date:
            logger.debug("Fetching new data")
            params['periodStart'] = start_date.strftime('%Y%m%d%H%M')
            params['periodEnd'] = end_date.strftime('%Y%m%d%H%M')
            xml_data = self._make_request(params)
            new_df = self._parse_xml_to_dataframe(xml_data)
            
            if cached_data is not None:
                logger.debug("Merging new data with cached data")
                df = pd.concat([cached_data[0], new_df]).drop_duplicates(subset=['start_time', 'psr_type'], keep='last')
            else:
                df = new_df
            
            if not df.empty:
                metadata = {
                    'country_code': country_code,
                    'start_date': df['start_time'].min().isoformat(),
                    'end_date': df['start_time'].max().isoformat(),
                }
                self._save_to_cache(cache_key, df, metadata)
                logger.debug(f"Saved to cache: {metadata}")
        else:
            logger.debug("Using existing cached data")
            df = cached_data[0]
        
        result = self._resample_to_standard_granularity(df[(df['start_time'] >= start_date) & (df['start_time'] < end_date)])
        logger.debug(f"Returning result with shape: {result.shape}")
        return result
    
    async def _make_async_request(self, session: aiohttp.ClientSession, params: Dict[str, Any]) -> str:
        params['securityToken'] = self.security_token
        async with session.get(self.BASE_URL, params=params) as response:
            response.raise_for_status()
            return await response.text()
    
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
                tasks.append(self._make_async_request(session, chunk_params))
                start_date = chunk_end_date
            return await asyncio.gather(*tasks)
    
    async def get_generation_data_async(self, country_code: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:

        params = {
            'documentType': 'A75',
            'processType': 'A16',
            'in_Domain': country_code,
            'outBiddingZone_Domain': country_code,
        }
        cache_key = self._get_cache_key(params)
        cached_data = self._load_from_cache(cache_key)
        
        logger.debug(f"Requested date range: {start_date} to {end_date}")
        
        if cached_data is not None:
            df, metadata = cached_data
            cached_start = pd.to_datetime(metadata['start_date'], utc=True)
            cached_end = pd.to_datetime(metadata['end_date'], utc=True)
            
            logger.debug(f"Cached data range: {cached_start} to {cached_end}")
            
            if cached_start <= start_date and cached_end >= end_date:
                logger.debug("Using cached data")
                return df[(df['start_time'] >= start_date) & (df['start_time'] < end_date)]
            
            # If there's overlap, adjust the request range
            if cached_end > start_date:
                start_date = cached_end
                logger.debug(f"Adjusted start_date to {start_date}")
        
        # If we need to fetch new data
        logger.debug("Fetching new data")
        xml_chunks = await self._fetch_data_in_chunks(params, start_date, end_date)
        new_df = pd.concat([self._parse_xml_to_dataframe(xml) for xml in xml_chunks], ignore_index=True)
        
        if cached_data is not None:
            df = pd.concat([cached_data[0], new_df]).drop_duplicates(subset=['start_time', 'psr_type'], keep='last')
        else:
            df = new_df
        
        if not df.empty:
            metadata = {
                'country_code': country_code,
                'start_date': df['start_time'].min().isoformat(),
                'end_date': df['start_time'].max().isoformat(),
            }
            self._save_to_cache(cache_key, df, metadata)
            logger.debug(f"Saved to cache: {metadata}")
        
        result = self._resample_to_standard_granularity(df[(df['start_time'] >= start_date) & (df['start_time'] < end_date)])
        logger.debug(f"Returning result with shape: {result.shape}")
        return result

    async def get_physical_flows_async(self, in_domain: str, out_domain: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        params = {
            'documentType': 'A11',
            'in_Domain': in_domain,
            'out_Domain': out_domain,
        }
        cache_key = self._get_cache_key(params)
        cached_data = self._load_from_cache(cache_key)
        
        if cached_data is not None:
            df, metadata = cached_data
            latest_cache_date = df['start_time'].max()
            if latest_cache_date >= end_date:
                return df[df['start_time'].between(start_date, end_date)]
            start_date = latest_cache_date
        
        xml_chunks = await self._fetch_data_in_chunks(params, start_date, end_date)
        new_df = pd.concat([self._parse_xml_to_dataframe(xml) for xml in xml_chunks], ignore_index=True)
        
        if cached_data is not None:
            df = pd.concat([df, new_df]).drop_duplicates(subset=['start_time', 'psr_type'], keep='last')
        else:
            df = new_df
        
        if df.empty:
            return df

        metadata = {
            'in_domain': in_domain,
            'out_domain': out_domain,
            'start_date': df['start_time'].min().isoformat(),
            'end_date': df['start_time'].max().isoformat(),
            'resolution': df['resolution'].iloc[0] if 'resolution' in df.columns else None
        }
        self._save_to_cache(cache_key, df, metadata)
        
        return df[df['start_time'].between(start_date, end_date)]

    def get_portugal_data(self, start_date: datetime, end_date: datetime) -> Dict[str, pd.DataFrame]:
        loop = asyncio.get_event_loop()
        generation = loop.run_until_complete(self.get_generation_data_async('10YPT-REN------W', start_date, end_date))
        imports = loop.run_until_complete(self.get_physical_flows_async('10YES-REE------0', '10YPT-REN------W', start_date, end_date))
        exports = loop.run_until_complete(self.get_physical_flows_async('10YPT-REN------W', '10YES-REE------0', start_date, end_date))
        return {'generation': generation, 'imports': imports, 'exports': exports}

    def get_spain_data(self, start_date: datetime, end_date: datetime) -> Dict[str, pd.DataFrame]:
        loop = asyncio.get_event_loop()
        generation = loop.run_until_complete(self.get_generation_data_async('10YES-REE------0', start_date, end_date))
        return {'generation': generation}
    
    def _resample_to_standard_granularity(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df

        df['start_time'] = df['start_time'].apply(self._ensure_naive_datetime)
        df = df.sort_values('start_time').set_index('start_time')
        
        # Group by psr_type and resample
        resampled_data = []
        for psr_type, group in df.groupby('psr_type'):
            resampled = group['quantity'].resample(
                self.STANDARD_GRANULARITY, 
                offset='0H',  # Start periods at 00 minutes
                label='left',  # Use the start of the period as the label
                closed='left'  # Include the left boundary of the interval
            ).mean()
            
            resampled = resampled.reset_index()
            resampled['psr_type'] = psr_type
            resampled['end_time'] = resampled['start_time'] + self.STANDARD_GRANULARITY
            resampled_data.append(resampled)
        
        if not resampled_data:
            return pd.DataFrame(columns=['start_time', 'end_time', 'psr_type', 'quantity', 'resolution'])

        result = pd.concat(resampled_data, ignore_index=True)
        result['resolution'] = self.STANDARD_GRANULARITY
        
        return result
