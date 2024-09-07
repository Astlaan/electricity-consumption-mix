import requests
import pandas as pd
from datetime import datetime
import xml.etree.ElementTree as ET
import os
import json
import hashlib
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ENTSOEDataFetcher:
    BASE_URL = "https://web-api.tp.entsoe.eu/api"
    CACHE_DIR = "data_cache"
    
    def __init__(self, security_token: str):
        self.security_token = security_token
        os.makedirs(self.CACHE_DIR, exist_ok=True)
        logger.debug(f"ENTSOEDataFetcher initialized with token: {security_token[:5]}...")

    def _get_cache_key(self, params: Dict[str, Any]) -> str:
        param_str = json.dumps(params, sort_keys=True)
        cache_key = hashlib.md5(param_str.encode()).hexdigest()
        logger.debug(f"Generated cache key: {cache_key}")
        return cache_key

    def _save_to_cache(self, cache_key: str, data: pd.DataFrame, metadata: Dict[str, Any]):
        cache_file = os.path.join(self.CACHE_DIR, f"{cache_key}.parquet")
        data.to_parquet(cache_file)
        with open(os.path.join(self.CACHE_DIR, f"{cache_key}_metadata.json"), 'w') as f:
            json.dump(metadata, f)
        logger.debug(f"Data saved to cache: {cache_file}")

    def _load_from_cache(self, cache_key: str) -> Optional[tuple]:
        cache_file = os.path.join(self.CACHE_DIR, f"{cache_key}.parquet")
        metadata_file = os.path.join(self.CACHE_DIR, f"{cache_key}_metadata.json")
        if os.path.exists(cache_file) and os.path.exists(metadata_file):
            logger.debug(f"Loading data from cache: {cache_file}")
            data = pd.read_parquet(cache_file)
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            return data, metadata
        logger.debug(f"No cache found for key: {cache_key}")
        return None

    def _make_request(self, params: Dict[str, Any]) -> str:
        params['securityToken'] = self.security_token
        logger.debug(f"Making request with params: {params}")
        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise

    def _parse_xml_to_dataframe(self, xml_data: str) -> pd.DataFrame:
        logger.debug("Parsing XML to DataFrame")
        root = ET.fromstring(xml_data)
        data = []
        namespace = {'ns': root.tag.split('}')[0].strip('{')}
        
        time_series_elements = root.findall(".//ns:TimeSeries", namespace)
        if not time_series_elements:
            logger.warning("No TimeSeries elements found in the XML")
            return pd.DataFrame(columns=['start_time', 'position', 'quantity', 'psr_type', 'resolution', 'in_domain', 'out_domain'])
        
        for time_series in time_series_elements:
            psr_type = time_series.find(".//ns:psrType", namespace)
            psr_type = psr_type.text if psr_type is not None else "Unknown"
            
            in_domain = time_series.find(".//ns:in_Domain.mRID", namespace)
            out_domain = time_series.find(".//ns:out_Domain.mRID", namespace)
            
            period_elements = time_series.findall(".//ns:Period", namespace)
            if not period_elements:
                logger.warning(f"No Period elements found for TimeSeries with psr_type: {psr_type}")
                continue
            
            for period in period_elements:
                start_time = period.find(".//ns:start", namespace)
                resolution = period.find(".//ns:resolution", namespace)
                
                if start_time is None or resolution is None:
                    logger.warning(f"Missing start_time or resolution for Period in TimeSeries with psr_type: {psr_type}")
                    continue
                
                start_time = start_time.text
                resolution = resolution.text
                
                point_elements = period.findall(".//ns:Point", namespace)
                if not point_elements:
                    logger.warning(f"No Point elements found for Period starting at {start_time}")
                    continue
                
                for point in point_elements:
                    position = point.find(".//ns:position", namespace)
                    quantity = point.find(".//ns:quantity", namespace)
                    
                    if position is None or quantity is None:
                        logger.warning(f"Missing position or quantity for Point in Period starting at {start_time}")
                        continue
                    
                    data_point = {
                        'start_time': start_time,
                        'position': int(position.text),
                        'quantity': float(quantity.text),
                        'psr_type': psr_type,
                        'resolution': resolution
                    }
                    
                    if in_domain is not None:
                        data_point['in_domain'] = in_domain.text
                    if out_domain is not None:
                        data_point['out_domain'] = out_domain.text
                    
                    data.append(data_point)
        
        if not data:
            logger.warning("No valid data points found in the XML")
            return pd.DataFrame(columns=['start_time', 'position', 'quantity', 'psr_type', 'resolution', 'in_domain', 'out_domain'])
        
        df = pd.DataFrame(data)
        df['start_time'] = pd.to_datetime(df['start_time'])
        logger.debug(f"Parsed DataFrame shape: {df.shape}")
        return df

    def get_generation_data(self, country_code: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        logger.debug(f"Getting generation data for {country_code} from {start_date} to {end_date}")
        params = {
            'documentType': 'A75',
            'processType': 'A16',
            'in_Domain': country_code,
            'outBiddingZone_Domain': country_code,
            'periodStart': start_date.strftime('%Y%m%d%H%M'),
            'periodEnd': end_date.strftime('%Y%m%d%H%M')
        }
        cache_key = self._get_cache_key(params)
        cached_data = self._load_from_cache(cache_key)
        
        if cached_data is not None:
            logger.debug("Using cached data")
            return cached_data[0]  # Return just the DataFrame, not the metadata
        
        logger.debug("Fetching new data")
        xml_data = self._make_request(params)
        df = self._parse_xml_to_dataframe(xml_data)
        if not df.empty:
            metadata = {
                'country_code': country_code,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'resolution': df['resolution'].iloc[0] if 'resolution' in df.columns else None
            }
            self._save_to_cache(cache_key, df, metadata)
        return df

    def get_physical_flows(self, in_domain: str, out_domain: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        logger.debug(f"Getting physical flows from {in_domain} to {out_domain} from {start_date} to {end_date}")
        params = {
            'documentType': 'A11',
            'in_Domain': in_domain,
            'out_Domain': out_domain,
            'periodStart': start_date.strftime('%Y%m%d%H%M'),
            'periodEnd': end_date.strftime('%Y%m%d%H%M')
        }
        cache_key = self._get_cache_key(params)
        cached_data = self._load_from_cache(cache_key)
        
        if cached_data is not None:
            logger.debug("Using cached data")
            return cached_data[0]  # Return just the DataFrame, not the metadata
        
        logger.debug("Fetching new data")
        xml_data = self._make_request(params)
        df = self._parse_xml_to_dataframe(xml_data)
        if not df.empty:
            metadata = {
                'in_domain': in_domain,
                'out_domain': out_domain,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'resolution': df['resolution'].iloc[0] if 'resolution' in df.columns else None
            }
            self._save_to_cache(cache_key, df, metadata)
        return df

    def get_portugal_data(self, start_date: datetime, end_date: datetime) -> Dict[str, pd.DataFrame]:
        logger.debug(f"Getting Portugal data from {start_date} to {end_date}")
        generation = self.get_generation_data('10YPT-REN------W', start_date, end_date)
        imports = self.get_physical_flows('10YES-REE------0', '10YPT-REN------W', start_date, end_date)
        exports = self.get_physical_flows('10YPT-REN------W', '10YES-REE------0', start_date, end_date)
        return {'generation': generation, 'imports': imports, 'exports': exports}

    def get_spain_data(self, start_date: datetime, end_date: datetime) -> Dict[str, pd.DataFrame]:
        logger.debug(f"Getting Spain data from {start_date} to {end_date}")
        generation = self.get_generation_data('10YES-REE------0', start_date, end_date)
        if not generation.empty:
            logger.debug(f"Spain generation data range: {generation['start_time'].min()} to {generation['start_time'].max()}")
        return {'generation': generation}
