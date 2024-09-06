import requests
import pandas as pd
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

class ENTSOEDataFetcher:
    BASE_URL = "https://web-api.tp.entsoe.eu/api"
    
    def __init__(self, security_token):
        self.security_token = security_token

    def _make_request(self, params):
        params['securityToken'] = self.security_token
        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()
        return response.text

    def _parse_xml_to_dataframe(self, xml_data):
        root = ET.fromstring(xml_data)
        data = []
        for time_series in root.findall(".//TimeSeries"):
            psr_type = time_series.find(".//psrType").text if time_series.find(".//psrType") is not None else "Unknown"
            for period in time_series.findall(".//Period"):
                start_time = period.find(".//start").text
                for point in period.findall(".//Point"):
                    position = point.find(".//position").text
                    quantity = point.find(".//quantity").text
                    data.append({
                        'start_time': start_time,
                        'position': int(position),
                        'quantity': float(quantity),
                        'psr_type': psr_type
                    })
        return pd.DataFrame(data)

    def get_generation_data(self, country_code, start_date, end_date):
        params = {
            'documentType': 'A75',
            'processType': 'A16',
            'in_Domain': country_code,
            'outBiddingZone_Domain': country_code,
            'periodStart': start_date.strftime('%Y%m%d%H%M'),
            'periodEnd': end_date.strftime('%Y%m%d%H%M')
        }
        xml_data = self._make_request(params)
        return self._parse_xml_to_dataframe(xml_data)

    def get_physical_flows(self, in_domain, out_domain, start_date, end_date):
        params = {
            'documentType': 'A11',
            'in_Domain': in_domain,
            'out_Domain': out_domain,
            'periodStart': start_date.strftime('%Y%m%d%H%M'),
            'periodEnd': end_date.strftime('%Y%m%d%H%M')
        }
        xml_data = self._make_request(params)
        return self._parse_xml_to_dataframe(xml_data)

    def get_portugal_data(self, start_date, end_date):
        generation = self.get_generation_data('10YPT-REN------W', start_date, end_date)
        imports = self.get_physical_flows('10YES-REE------0', '10YPT-REN------W', start_date, end_date)
        exports = self.get_physical_flows('10YPT-REN------W', '10YES-REE------0', start_date, end_date)
        return {'generation': generation, 'imports': imports, 'exports': exports}

    def get_spain_data(self, start_date, end_date):
        generation = self.get_generation_data('10YES-REE------0', start_date, end_date)
        imports_fr = self.get_physical_flows('10YFR-RTE------C', '10YES-REE------0', start_date, end_date)
        exports_fr = self.get_physical_flows('10YES-REE------0', '10YFR-RTE------C', start_date, end_date)
        return {'generation': generation, 'imports_fr': imports_fr, 'exports_fr': exports_fr}

    def get_france_data(self, start_date, end_date):
        generation = self.get_generation_data('10YFR-RTE------C', start_date, end_date)
        return {'generation': generation}
