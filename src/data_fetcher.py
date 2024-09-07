import requests
import pandas as pd
from datetime import datetime
import xml.etree.ElementTree as ET
import os
import json
import hashlib
from typing import Dict, Any, Optional

class ENTSOEDataFetcher:
    BASE_URL = "https://web-api.tp.entsoe.eu/api"
    CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data_cache")
    
    def __init__(self, security_token: str):
        self.security_token = security_token
        os.makedirs(self.CACHE_DIR, exist_ok=True)

    def _get_cache_key(self, params: Dict[str, Any]) -> str:
        param_str = json.dumps(params, sort_keys=True)
        cache_key = hashlib.md5(param_str.encode()).hexdigest()
        return cache_key

    def _save_to_cache(self, cache_key: str, data: pd.DataFrame, metadata: Dict[str, Any]):
        cache_file = os.path.join(self.CACHE_DIR, f"{cache_key}.parquet")
        data.to_parquet(cache_file)
        
        # Convert Timedelta to string representation
        if 'resolution' in metadata and isinstance(metadata['resolution'], pd.Timedelta):
            metadata['resolution'] = str(metadata['resolution'])
        
        with open(os.path.join(self.CACHE_DIR, f"{cache_key}_metadata.json"), 'w') as f:
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

    def _make_request(self, params: Dict[str, Any]) -> str:
        params['securityToken'] = self.security_token
        print(f"Making API request with params: {params}")
        try:
            response = requests.get(self.BASE_URL, params=params)
            print(f"API response status code: {response.status_code}")
            if response.status_code != 200:
                print(f"API error response: {response.text}")
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Request failed: {str(e)}")
            raise

    def _parse_xml_to_dataframe(self, xml_data: str) -> pd.DataFrame:
        root = ET.fromstring(xml_data)
        data = []
        namespace = {'ns': root.tag.split('}')[0].strip('{')}
        
        time_series_elements = root.findall(".//ns:TimeSeries", namespace)
        if not time_series_elements:
            print("No TimeSeries elements found in the XML")
            return pd.DataFrame(columns=['start_time', 'end_time', 'quantity', 'psr_type', 'resolution', 'in_domain', 'out_domain'])
        
        for time_series in time_series_elements:
            psr_type = time_series.find(".//ns:psrType", namespace)
            psr_type = psr_type.text if psr_type is not None else "Unknown"
            
            in_domain = time_series.find(".//ns:in_Domain.mRID", namespace)
            out_domain = time_series.find(".//ns:out_Domain.mRID", namespace)
            
            period_elements = time_series.findall(".//ns:Period", namespace)
            if not period_elements:
                print(f"No Period elements found for TimeSeries with psr_type: {psr_type}")
                continue
            
            for period in period_elements:
                start_time = period.find(".//ns:start", namespace)
                resolution = period.find(".//ns:resolution", namespace)
                
                if start_time is None or resolution is None:
                    print(f"Missing start_time or resolution for Period in TimeSeries with psr_type: {psr_type}")
                    continue
                
                start_time = pd.to_datetime(start_time.text)
                resolution = pd.Timedelta(resolution.text)
                
                point_elements = period.findall(".//ns:Point", namespace)
                if not point_elements:
                    print(f"No Point elements found for Period starting at {start_time}")
                    continue
                
                for point in point_elements:
                    position = point.find(".//ns:position", namespace)
                    quantity = point.find(".//ns:quantity", namespace)
                    
                    if position is None or quantity is None:
                        print(f"Missing position or quantity for Point in Period starting at {start_time}")
                        continue
                    
                    point_start_time = start_time + resolution * (int(position.text) - 1)
                    point_end_time = point_start_time + resolution
                    
                    data_point = {
                        'start_time': point_start_time,
                        'end_time': point_end_time,
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
            print("No valid data points found in the XML")
            return pd.DataFrame(columns=['start_time', 'end_time', 'quantity', 'psr_type', 'resolution', 'in_domain', 'out_domain'])
        
        return pd.DataFrame(data)

    def get_generation_data(self, country_code: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
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
            df = cached_data[0]
        else:
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
            return cached_data[0]  # Return just the DataFrame, not the metadata
        
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
        generation = self.get_generation_data('10YPT-REN------W', start_date, end_date)
        imports = self.get_physical_flows('10YES-REE------0', '10YPT-REN------W', start_date, end_date)
        exports = self.get_physical_flows('10YPT-REN------W', '10YES-REE------0', start_date, end_date)
        return {'generation': generation, 'imports': imports, 'exports': exports}

    def get_spain_data(self, start_date: datetime, end_date: datetime) -> Dict[str, pd.DataFrame]:
        generation = self.get_generation_data('10YES-REE------0', start_date, end_date)
        return {'generation': generation}
