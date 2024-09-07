import requests
import pandas as pd
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import os
import json
import hashlib

class ENTSOEDataFetcher:
    BASE_URL = "https://web-api.tp.entsoe.eu/api"
    CACHE_DIR = "data_cache"
    
    def __init__(self, security_token):
        self.security_token = security_token
        os.makedirs(self.CACHE_DIR, exist_ok=True)

    def _get_cache_key(self, params):
        # Create a unique cache key based on the request parameters
        param_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(param_str.encode()).hexdigest()

    def _save_to_cache(self, cache_key, data):
        cache_file = os.path.join(self.CACHE_DIR, f"{cache_key}.csv")
        data.to_csv(cache_file, index=False)

    def _load_from_cache(self, cache_key):
        cache_file = os.path.join(self.CACHE_DIR, f"{cache_key}.csv")
        if os.path.exists(cache_file):
            return pd.read_csv(cache_file, parse_dates=['start_time'])
        return None

    def _make_request(self, params):
        params['securityToken'] = self.security_token
        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()
        xml_response = response.text
        print(f"Raw XML response:\n{xml_response[:1000]}...")  # Print first 1000 characters
        return xml_response

    def _parse_xml_to_dataframe(self, xml_data):
        root = ET.fromstring(xml_data)
        data = []
        namespace = {'ns': root.tag.split('}')[0].strip('{')}
        
        for time_series in root.findall(".//ns:TimeSeries", namespace):
            psr_type = time_series.find(".//ns:psrType", namespace)
            psr_type = psr_type.text if psr_type is not None else "Unknown"
            
            in_domain = time_series.find(".//ns:in_Domain.mRID", namespace)
            out_domain = time_series.find(".//ns:out_Domain.mRID", namespace)
            
            for period in time_series.findall(".//ns:Period", namespace):
                start_time = period.find(".//ns:start", namespace).text
                resolution = period.find(".//ns:resolution", namespace).text
                
                for point in period.findall(".//ns:Point", namespace):
                    position = point.find(".//ns:position", namespace).text
                    quantity = point.find(".//ns:quantity", namespace).text
                    
                    data_point = {
                        'start_time': start_time,
                        'position': int(position),
                        'quantity': float(quantity),
                        'psr_type': psr_type,
                        'resolution': resolution
                    }
                    
                    if in_domain is not None:
                        data_point['in_domain'] = in_domain.text
                    if out_domain is not None:
                        data_point['out_domain'] = out_domain.text
                    
                    data.append(data_point)
        
        df = pd.DataFrame(data)
        if not df.empty:
            df['start_time'] = pd.to_datetime(df['start_time'])
        return df

    def get_generation_data(self, country_code, start_date, end_date):
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
            return cached_data
        
        xml_data = self._make_request(params)
        df = self._parse_xml_to_dataframe(xml_data)
        self._save_to_cache(cache_key, df)
        return df

    def get_physical_flows(self, in_domain, out_domain, start_date, end_date):
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
            return cached_data
        
        xml_data = self._make_request(params)
        df = self._parse_xml_to_dataframe(xml_data)
        self._save_to_cache(cache_key, df)
        return df

    def get_portugal_data(self, start_date, end_date):
        generation = self.get_generation_data('10YPT-REN------W', start_date, end_date)
        imports = self.get_physical_flows('10YES-REE------0', '10YPT-REN------W', start_date, end_date)
        exports = self.get_physical_flows('10YPT-REN------W', '10YES-REE------0', start_date, end_date)
        return {'generation': generation, 'imports': imports, 'exports': exports}

    def get_spain_data(self, start_date, end_date):
        generation = self.get_generation_data('10YES-REE------0', start_date, end_date)
        if not generation.empty:
            print(f"Spain generation data range: {generation['start_time'].min()} to {generation['start_time'].max()}")
        return {'generation': generation}
