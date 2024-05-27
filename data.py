import pandas as pd
import sqlite3
from sklearn.cluster import KMeans 
import os

db_name = "sales.db"

def abs_file_path(filename):
    script_dir = os.path.dirname(__file__)
    absolute_path = os.path.join(script_dir, filename)
    return absolute_path

def db_connect(query):
    connect = sqlite3.connect(abs_file_path(db_name))
    df = pd.read_sql_query(query,connect)
    return df

#Queries:
query_total_sales = "select round(sum(RPTG_AMT)/1000000) as Sales from CN_ORDERS_HR_AGG"
query_city_count = "select count(distinct SHIP_TO_CITY_CD) as City_Count from CN_ORDERS_HR_AGG"
query_district_count = "select count(distinct SHIP_TO_DISTRICT_NAME) as District_Count from CN_ORDERS_HR_AGG"
query_per_hour_sales = "select ORDER_HOUR_PST,round(sum(RPTG_AMT)/1000000) as RPTG_AMT from CN_ORDERS_HR_AGG group by 1 order by 1"
query_avg_per_hour_sales = "select SHIP_TO_CITY_CD_EN||'('||SHIP_TO_CITY_CD||')' as SHIP_TO_CITY,round(avg(RPTG_AMT)/1000000) as RPTG_AMT from (select SHIP_TO_CITY_CD_EN,SHIP_TO_CITY_CD,ORDER_HOUR_PST,sum(RPTG_AMT) as RPTG_AMT from CN_ORDERS_HR_AGG group by 1,2,3)a group by 1 order by 2 desc limit 10"
query_avg_sales_by_district = "select SHIP_TO_CITY_CD_EN||'('||SHIP_TO_CITY_CD||')' as SHIP_TO_CITY,round(avg(RPTG_AMT)/1000000) as RPTG_AMT from (select SHIP_TO_CITY_CD_EN,SHIP_TO_CITY_CD,SHIP_TO_DISTRICT_NAME,sum(RPTG_AMT) as RPTG_AMT from CN_ORDERS_HR_AGG group by 1,2,3)a group by 1 order by 2 desc limit 10"
query_cluster = "select SHIP_TO_CITY_CD,sum(RPTG_AMT) as RPTG_AMT from CN_ORDERS_HR_AGG group by 1"
query_corr ="select SHIP_TO_CITY_CD_EN||'('||SHIP_TO_CITY_CD||')' as SHIP_TO_CITY, count(distinct SHIP_TO_DISTRICT_NAME) as DISTRICT_COUNT,sum(RPTG_AMT) RPTG_AMT from CN_ORDERS_HR_AGG group by 1 order by 3 desc"
query_highest_sales_city ="select SHIP_TO_CITY_CD_EN||'('||SHIP_TO_CITY_CD||')' as SHIP_TO_CITY, count(distinct SHIP_TO_DISTRICT_NAME) as DISTRICT_COUNT,sum(RPTG_AMT) RPTG_AMT from CN_ORDERS_HR_AGG group by 1 order by 3 desc"
query_District_Count_Sales ="select SHIP_TO_CITY,'Number of Districts: '||District_Count as District_Count,round(RPTG_AMT/1000000) as RPTG_AMT from (select SHIP_TO_CITY_CD_EN||'('||SHIP_TO_CITY_CD||')' as SHIP_TO_CITY,count(distinct SHIP_TO_DISTRICT_NAME) as District_Count, sum(RPTG_AMT) RPTG_AMT,ROW_NUMBER() OVER (order by sum(RPTG_AMT) desc) as ronum_sales,ROW_NUMBER() OVER (order by count(distinct SHIP_TO_DISTRICT_NAME) desc) as ronum_city_count from CN_ORDERS_HR_AGG group by 1)a where (ronum_sales=1 or ronum_city_count=1)"
#creating the Dataframes:

#dataframe for getting the total sales:
df_total_Sales = db_connect(query_total_sales)
total_Sales = df_total_Sales.iloc[0]["Sales"]

#dataframe for getting the city count:
df_city_count = db_connect(query_city_count)
total_city_count = df_city_count.iloc[0]["City_Count"]

#dataframe for getting district count:
df_district_count = db_connect(query_district_count)
total_district_count = df_district_count.iloc[0]["District_Count"]

#dataframe for getting the hourly sales trend
df_per_hour_sales = db_connect(query_per_hour_sales)

#dataframe for getting the top 10 cities by per-hour sales
df_avg_per_hour_sales = db_connect(query_avg_per_hour_sales)

#to get the data for top 10 cities by avg sales by district
df_avg_sales_by_district = db_connect(query_avg_sales_by_district)

#dataframe for clusetring data
df_cluster= db_connect(query_cluster)

#datafrme for correlation:
df_corr = db_connect(query_corr)

#dataframe for getting the highest sales and highest district count and their cities:
df_District_Count_Sales = db_connect(query_District_Count_Sales)


#Clusetring:
#Initialze the model
kmeans = KMeans(n_clusters=7,random_state =42)

#Fit the model to the data
kmeans.fit_predict(df_cluster[["RPTG_AMT"]])

#get the cluster labels
df_cluster['Cluster'] = kmeans.labels_

#sort the data by avg of the amount by clusters
df_cluster_avg = df_cluster.groupby("Cluster")["RPTG_AMT"].mean().sort_values(ascending= False).reset_index()

#create the Tier column:
df_cluster_avg["Tiers"] =df_cluster_avg.index + 1
df_cluster_avg["Tiers"] = 'Tier ' + df_cluster_avg["Tiers"].astype(str)

#dropping the amount column:
df_cluster_avg.drop(["RPTG_AMT"],axis = 1 ,inplace= True)

#Assign the Tiers to the sales data based on the cluster column:
df_sales_city_tier = df_cluster.merge(df_cluster_avg,how='left',left_on='Cluster',right_on='Cluster')

#getting a dataframe having the sum of sales and count of cities by City Tier
df_sales_tier_amt = df_sales_city_tier.groupby("Tiers")["RPTG_AMT"].sum().reset_index()
df_sales_tier_city = df_sales_city_tier.groupby("Tiers")["SHIP_TO_CITY_CD"].count().reset_index()
df_sales_tier_city.rename(columns = {'SHIP_TO_CITY_CD':'SHIP_TO_CITY_CD_COUNT'}, inplace = True)
df_sales_tier_amt_city = df_sales_tier_amt.merge(df_sales_tier_city , how ="inner" , left_on='Tiers',right_on='Tiers')
df_sales_tier_amt_city["RPTG_AMT_Millions"] = df_sales_tier_amt_city["RPTG_AMT"]/1000000
df_sales_tier_amt_city = df_sales_tier_amt_city.round({"RPTG_AMT_Millions" : 0})

#getting the Corr value between the count of districts and sales for cities:
df_corr_new = df_corr[["DISTRICT_COUNT","RPTG_AMT"]]

corr = df_corr_new.corr()
corr_value = round(corr["RPTG_AMT"][0],2)
