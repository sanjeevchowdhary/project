from flask import Flask , render_template
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import data

app = Flask(__name__)

@app.get("/")
def graphs():
    
    #plot for the total sales,city count,district count
    fig1 = go.Figure()

    fig1.add_trace(go.Indicator(
        mode = "number",
        value = data.total_Sales,
        domain = {'x': [0, 0.5], 'y': [0, 0]},
        number = {"suffix": "m", "font":{"size":50}},
        title = {"text": "Total Sales(RMB)"}
        
        ))

    fig1.add_trace(go.Indicator(
        mode = "number",
        value = data.total_city_count,
        domain = {'x': [0, 1], 'y': [0, 0]},
        number = {"font":{"size":50}},
        title = {"text": "Total Number of Cities"}
        ))

    fig1.add_trace(go.Indicator(
        mode = "number",
        value = data.total_district_count,
        domain = {'x': [0.5, 1], 'y': [0, 0]},
        number = {"font":{"size":50}},
        title = {"text": "Total Number of Districts"}
        ))
    fig1.update_layout(paper_bgcolor="LightSteelBlue")
    graph1 = pio.to_html(fig1, full_html=False)


    #plot for sales trend by hour
    fig2 = px.line(data.df_per_hour_sales , x="ORDER_HOUR_PST", y ="RPTG_AMT" , title="Hourly Sales Trend" , labels= {"ORDER_HOUR_PST":"Hour" , "RPTG_AMT":"Sales in Millions(RMB)"}, text="RPTG_AMT").update_layout(xaxis_title = "Hour" , yaxis_title = "Sales in Millions(RMB)")
    fig2.update_traces(textposition="top center")
    graph2 = pio.to_html(fig2, full_html=False)


    #plot for :Top 10 cities by per hour sales
    fig3 = px.bar(data.df_avg_per_hour_sales , x="SHIP_TO_CITY", y ="RPTG_AMT" , title="Top 10 cities by per hour sales" , text_auto=True , labels= {"SHIP_TO_CITY":"City" , "RPTG_AMT":"Sales in Millions(RMB)"}).update_layout(xaxis_title = "City" , yaxis_title = "Sales in Millions(RMB)")
    graph3 = pio.to_html(fig3, full_html=False)

    #plot for :Top 10 cities by average sales by district
    fig4 = px.bar(data.df_avg_sales_by_district , x="SHIP_TO_CITY", y ="RPTG_AMT" , title="Top 10 cities by average sales by district" , text_auto=True, labels= {"SHIP_TO_CITY":"City" , "RPTG_AMT":"Sales in Millions(RMB)"}).update_layout(xaxis_title = "City" , yaxis_title = "Sales in Millions(RMB)")
    graph4 = pio.to_html(fig4, full_html=False)

    #Plots for sales distribution by city Tier and Number of citites in each Tier
    fig5 = px.pie(data.df_sales_tier_amt_city, values='RPTG_AMT_Millions', names='Tiers', title='Sales Distribution By City Tiers', color_discrete_sequence=px.colors.qualitative.Set3 , labels= {"RPTG_AMT_Millions":"Sales(in Millions)","Tiers":"City Tiers"}).update_traces(sort=False)
    fig6 = px.bar(data.df_sales_tier_amt_city , x="Tiers", y ="SHIP_TO_CITY_CD_COUNT" ,title="Number of Cities Per Tier" , labels= {"Tiers":"City Tiers" , "SHIP_TO_CITY_CD_COUNT":"City Count"}).update_layout(xaxis_title = "City Tiers" , yaxis_title = "City Count")

    graph5 = pio.to_html(fig5, full_html=False)
    graph6 = pio.to_html(fig6, full_html=False)

    #plot for correaltion between number of districts in a city vs sales in the city

    fig7 = go.Figure()

    fig7.add_trace(go.Indicator(
        mode = "number",
        value = data.corr_value,
        domain = {'x': [0.5, 0.5], 'y': [0, 0]},
        number = {"font":{"size":50}},
        title = {"text": "Correlation between number of districts in a city vs sales in the city"}
        
        ))
    fig7.update_layout(paper_bgcolor="LightSteelBlue")
       
    graph7 = pio.to_html(fig7, full_html=False)

    #Cities with Highest Sales and Most Districts
    fig8 = px.bar(data.df_District_Count_Sales , x="SHIP_TO_CITY", y ="RPTG_AMT" , title="Cities with Highest Sales and Most Districts" ,text="District_Count" , labels= {"SHIP_TO_CITY":"City" , "RPTG_AMT":"Sales in Millions(RMB)", "District_Count":"Districts"}).update_layout(xaxis_title = "City" , yaxis_title = "Sales in Millions(RMB)")
    fig8.update_traces(width=0.3,textfont_size=100, textangle=0, textposition="outside", cliponaxis=False)
    graph8 = pio.to_html(fig8, full_html=False)


    return render_template('ui.html', graph1=graph1, graph2=graph2, graph3=graph3, graph4=graph4, graph5=graph5, graph6=graph6, graph7=graph7, graph8=graph8 )



