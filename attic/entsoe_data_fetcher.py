    def get_generation_data(self, country_code: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        # Ensure input dates are naive UTC
        start_date = start_date.replace(tzinfo=None)
        end_date = end_date.replace(tzinfo=None)

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

        # If we need to fetch new data
        if cached_data is None:
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