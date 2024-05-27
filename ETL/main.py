import pandas as pd
import os
import sqlite3
from deep_translator import GoogleTranslator

fx = 7.16

#defining the required functions:

#getting the hour part from the HHMMSS:
def standardize_hour_str(time_str):
    time_str_new= time_str.zfill(6)
    return f"{time_str_new[:2]}"

#getting the absoloute file path:
def abs_file_path(filename):
    script_dir = os.path.dirname(__file__)
    absolute_path = os.path.join(script_dir, filename)
    return absolute_path

#converting chinese to english:
def chinese_translator(chinese_list):
    translated_batch=[]

    for i in range(0,len(chinese_list)):
        data = GoogleTranslator(source='chinese (traditional)', target='en').translate(chinese_list[i])
        translated_batch.append(data)
    return translated_batch

#Database connnection and insert data:
def db_insert(df):

    #Connect to SQLite database
    conn = sqlite3.connect('sales.db')
    # Write the DataFrame to the table:
    df.to_sql(
              'CN_ORDERS_HR_AGG', 
              conn, 
              if_exists='append',
              index=False,
              dtype={   
                        'SHIP_TO_CITY_CD': 'VARCHAR(200)',
                        'SHIP_TO_CITY_CD_EN': 'VARCHAR(200)',
                        'SHIP_TO_DISTRICT_NAME': 'VARCHAR(200)',
                        'SHIP_TO_DISTRICT_NAME_EN': 'VARCHAR(200)',
                        'ORDER_HOUR_PST': 'INTEGER',
                        'RPTG_AMT': 'decimal(18,2)',
                        'ORDER_QTY': 'INTEGER'
                    }
              )

    conn.close()


##read the first data set to dataframe
df_dataset1 = pd.read_excel(abs_file_path("dataset1.xlsx"),sheet_name="DATA")

##Remove any non numereic qty in the qty column
df_dataset1['ORDER_QTY'] = pd.to_numeric(df_dataset1['ORDER_QTY'], errors='coerce')
df_dataset1.dropna(inplace=True)

##Remove the time value in Order_Time and 999999 in CITY_DISTRICT_ID
df_dataset1 = df_dataset1[(df_dataset1["ORDER_TIME  (PST)"] != 'time') & (df_dataset1["CITY_DISTRICT_ID"] != 999999)]

##convert the USD to RMB
df_dataset1.loc[(df_dataset1["CURRENCY_CD"] == 'USD'), ["RPTG_AMT"]] = df_dataset1[(df_dataset1["CURRENCY_CD"] == 'USD')]["RPTG_AMT"]*fx
df_dataset1.loc[(df_dataset1["CURRENCY_CD"] == 'USD'), ["CURRENCY_CD"]] = 'RMB'


##read the mapping to dataframe
df_city_district_map = pd.read_excel(abs_file_path("dataset1.xlsx"),sheet_name="CITY_DISTRICT_MAP")

#translating chinese names to english:
list_ship_to_city_cd = df_city_district_map["SHIP_TO_CITY_CD"].to_list()
list_ship_to_district_name = df_city_district_map["SHIP_TO_DISTRICT_NAME"].to_list()

df_city_district_map['SHIP_TO_CITY_CD_EN'] = chinese_translator(list_ship_to_city_cd)
df_city_district_map['SHIP_TO_DISTRICT_NAME_EN'] = chinese_translator(list_ship_to_district_name)


##lookup the mapping for the dataset1 to get the SHIP_TO_CITY_CD and SHIP_TO_DISTRICT_NAME

df_dataset1_mapped = df_dataset1.merge(df_city_district_map,how='left',left_on='CITY_DISTRICT_ID',right_on='CITY_DISTRICT_ID')

#renaming Order timestamp column:
df_dataset1_mapped.rename(columns={'ORDER_TIME  (PST)':'ORDER_TIME_PST'}, inplace=True)

#getting the hour part only for the ORDER_TIME_PST:
df_dataset1_mapped["ORDER_HOUR_PST"] = df_dataset1_mapped["ORDER_TIME_PST"].astype('string').apply(standardize_hour_str)

#aggregating the data at the City,District,hour grain:
df_dataset1_agg = df_dataset1_mapped.groupby(['SHIP_TO_CITY_CD','SHIP_TO_CITY_CD_EN','SHIP_TO_DISTRICT_NAME','SHIP_TO_DISTRICT_NAME_EN','ORDER_HOUR_PST'],as_index=False).agg({'RPTG_AMT': 'sum', 'ORDER_QTY': 'sum'})

#creating the final data:
df_dataset1_mapped_final = df_dataset1_agg[['SHIP_TO_CITY_CD','SHIP_TO_CITY_CD_EN','SHIP_TO_DISTRICT_NAME','SHIP_TO_DISTRICT_NAME_EN','ORDER_HOUR_PST','RPTG_AMT','ORDER_QTY']]

df_dataset1_mapped_final= df_dataset1_mapped_final.astype(
{
    'SHIP_TO_CITY_CD':str,
    'SHIP_TO_CITY_CD_EN':str,
    'SHIP_TO_DISTRICT_NAME':str,
    'SHIP_TO_DISTRICT_NAME_EN':str,
    'ORDER_HOUR_PST':int,
    'RPTG_AMT':float,
    'ORDER_QTY':int
}
)

#captitlising the first Character for the SHIP_TO_CITY_CD_EN and SHIP_TO_DISTRICT_NAME_EN
df_dataset1_mapped_final["SHIP_TO_CITY_CD_EN"] = df_dataset1_mapped_final["SHIP_TO_CITY_CD_EN"].str.capitalize()
df_dataset1_mapped_final["SHIP_TO_DISTRICT_NAME_EN"] = df_dataset1_mapped_final["SHIP_TO_DISTRICT_NAME_EN"].str.capitalize()

##reading the json data set
df_dataset2 = pd.read_json(abs_file_path("dataset2.json"))

#getting the hour part of the ORDER_TIME_PST
df_dataset2["ORDER_HOUR_PST"] = df_dataset2["ORDER_TIME_PST"].astype('string').apply(standardize_hour_str)

#aggregating the data at the SHIP_TO_CITY_CD,SHIP_TO_DISTRICT_NAME,ORDER_HOUR_PST
df_dataset2_agg = df_dataset2.groupby(['SHIP_TO_CITY_CD','SHIP_TO_DISTRICT_NAME','ORDER_HOUR_PST'],as_index=False).agg({'RPTG_AMT': 'sum', 'ORDER_QTY': 'sum'})

#translating to english the SHIP_TO_CITY_CD and SHIP_TO_DISTRICT_NAME
#translating chinese names to english:
list_ship_to_city_data_set2 = df_dataset2_agg["SHIP_TO_CITY_CD"].to_list()
list_ship_to_district_name_data_set2 = df_dataset2_agg["SHIP_TO_DISTRICT_NAME"].to_list()

df_dataset2_agg['SHIP_TO_CITY_CD_EN'] = chinese_translator(list_ship_to_city_data_set2)
df_dataset2_agg['SHIP_TO_DISTRICT_NAME_EN'] = chinese_translator(list_ship_to_district_name_data_set2)

#preparing the final dataset2:
df_dataset2_final = df_dataset2_agg[['SHIP_TO_CITY_CD','SHIP_TO_CITY_CD_EN','SHIP_TO_DISTRICT_NAME','SHIP_TO_DISTRICT_NAME_EN','ORDER_HOUR_PST','RPTG_AMT','ORDER_QTY']]

df_dataset2_final= df_dataset2_final.astype(
{
    'SHIP_TO_CITY_CD':str,
    'SHIP_TO_CITY_CD_EN':str,
    'SHIP_TO_DISTRICT_NAME':str,
    'SHIP_TO_DISTRICT_NAME_EN':str,
    'ORDER_HOUR_PST':int,
    'RPTG_AMT':float,
    'ORDER_QTY':int
}
)

#captitlising the first Character for the SHIP_TO_CITY_CD_EN and SHIP_TO_DISTRICT_NAME_EN
df_dataset2_final["SHIP_TO_CITY_CD_EN"] = df_dataset2_final["SHIP_TO_CITY_CD_EN"].str.capitalize()
df_dataset2_final["SHIP_TO_DISTRICT_NAME_EN"] = df_dataset2_final["SHIP_TO_DISTRICT_NAME_EN"].str.capitalize()

#inserting to DB:
db_insert(df_dataset1_mapped_final)
db_insert(df_dataset2_final)
