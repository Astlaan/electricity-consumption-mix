data_first_two_hours = """
<GL_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-6:generationloaddocument:3:0">
  <mRID>f0e1d2c3b4a59687abcdef01234567</mRID>
  <revisionNumber>1</revisionNumber>
  <type>A75</type>
  <process.processType>A16</process.processType>
  <sender_MarketParticipant.mRID codingScheme="A01">10X1001A1001A450</sender_MarketParticipant.mRID>
  <sender_MarketParticipant.marketRole.type>A32</sender_MarketParticipant.marketRole.type>
  <receiver_MarketParticipant.mRID codingScheme="A01">10X1001A1001A450</receiver_MarketParticipant.mRID>
  <receiver_MarketParticipant.marketRole.type>A33</receiver_MarketParticipant.marketRole.type>
  <createdDateTime>2024-10-26T11:00:00Z</createdDateTime>
  <time_Period.timeInterval>
    <start>2024-01-01T00:00Z</start>
    <end>2024-01-01T02:00Z</end>  <!-- Adjusted end time -->
  </time_Period.timeInterval>
  <TimeSeries>
    <mRID>1</mRID>
    <businessType>A01</businessType>
    <objectAggregation>A08</objectAggregation>
    <inBiddingZone_Domain.mRID codingScheme="A01">10YPT-REN------W</inBiddingZone_Domain.mRID>
    <quantity_Measure_Unit.name>MAW</quantity_Measure_Unit.name>
    <curveType>A01</curveType>
    <MktPSRType>
      <psrType>B16</psrType>
    </MktPSRType>
    <Period>
      <timeInterval>
        <start>2024-01-01T00:00Z</start>
        <end>2024-01-01T02:00Z</end>  <!-- Adjusted end time -->
      </timeInterval>
      <resolution>PT60M</resolution>
      <Point>
        <position>1</position>
        <quantity>110</quantity>
      </Point>
      <Point>
        <position>2</position>
        <quantity>120</quantity>
      </Point>
    </Period>
  </TimeSeries>
</GL_MarketDocument>
"""