from scraping.dailyfx_com import dailyfx_com
from scraping.forexfactory_calendar import get_monthly_data
from scraping.investing_com import investing_com
from scraping.bloomberg_com import bloomberg_com
from scraping.tradingeconomics_calendar import fx_calendar

if __name__ == "__main__":
    #print(dailyfx_com())
    # print(investing_com())
    data = bloomberg_com()
    [print(x) for x in data]
    # fx_calendar("2024-11-10T00:00:00Z" , "2024-11-12T00:00:00Z")
    # Get data for a specific month and store in a DataFrame
    # month = "oct.2024"
    # monthly_data_df = get_monthly_data(month)
    # print(monthly_data_df)
