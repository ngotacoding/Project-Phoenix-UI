import scipy
import streamlit as st
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
import plotly.graph_objects as go
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import warnings
import numpy as np
import pandas as pd
pd.set_option("display.max_columns", None)

warnings.filterwarnings("ignore")


# Processing for insurance data
def preprocess_insurance_data(data):
    """
    Preprocessing steps for Insurance_claims_mendeleydata_6.csv
    to be transformed in a manner that allows for state-wise visualization

    Args
    ---------------
    data: pd.DataFrame | pandas dataframe to be used for state-wise plots

    Returns
    ---------------
    data : pd.DataFrame | preprocessed with minimal steps 

    Errors Raised
    ---------------
    KeyError | if data with different column names is used, then this function will raise an error

    """

    data = data.rename(columns={"total_claim_amount": "claim_amount",
                                "insured_sex": "gender"})
    data["gender"] = data["gender"].str.title()

    # Bins for Age Plots
    # bins = [-np.inf, 2, 12, 18, 35, 60, np.inf]
    # labels = ["Infant 0-2", "Child 2-12", "Teenager 12-18", "Young Adult 18-35",
    #       "Adult 35-60", "Senior Citizen 60+"]

    # Bins #2
    bins = [15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65]
    labels = ["15-20", "20-25", "25-30", "30-35", "35-40", "40-45", "45-50", "50-55", "55-60",
              "60-65"]

    data["age_bracket"] = pd.cut(data["age"], bins=bins, labels=labels)

    data = data.drop(columns=["policy_state", "policy_csl", "policy_deductable", "policy_annual_premium",
                     "umbrella_limit", "policy_number", "capital-gains", "capital-loss", "city", "injury_claim",
                              "property_claim", "vehicle_claim"])

    data["collision_type"] = data["collision_type"].str.replace(
        "?", "Unattended Vehicle")

    return data


# Statewise Plots -------------------------------------------

def plotly_states(data):
    """
    Function to generate a plotly figure of barplots of mean and median state claim values for car accidents
    compatible with sample_data_formatted.csv and Insurance_claims_mendeleydata_6.csv

    Args
    -----------
    data: pd.DataFrame | data with columns: ["state", "total_claim_amount"]

    Returns
    -----------
    plotly figure | barplot with hover values of State, Mean/Median Value 

    Errors
    -----------
    KeyError if data do not contain the correct columns
    """

    # Filtering out miscellaneous states
    data = data[data["state"] != "Other"]

    # Grouping data by state and calculating median and mean
    grouped = data.groupby("state")["claim_amount"].agg(
        ["median", "mean"]).sort_values(by="median", ascending=False)

    # Resetting index to make 'state' a column for Plotly
    grouped = grouped.reset_index()

    # Creating Plotly figure
    fig = px.bar(grouped, x='state', y=['median', 'mean'],
                 labels={'value': 'Claim Amount in USD', 'state': 'States'},
                 title='Mean and Median Claims by State Sorted by Median Claim',
                 barmode='group',
                 template="plotly")

    # Legend
    fig.update_layout(legend_title='')

    # Customizing hover info
    fig.update_traces(hovertemplate='State: %{x}<br>Value: %{y:$,.2f}')

    fig.for_each_trace(lambda t: t.update(name=t.name.capitalize()))
    fig.update_layout(yaxis=dict(tickformat='$,.2f'))
    # Returning the Plotly figure
    return fig


# Boxplots for State Car Accident Claim Distributions

def plotly_box_states(data):
    """
    Function to generate a plotly figure of boxplots of car accidents claim distributions by state
    compatible with sample_data_formatted.csv and Insurance_claims_mendeleydata_6.csv

    Args
    -----------
    data: pd.DataFrame | data with columns: ["state", "claim_amount"]

    Returns
    -----------
    plotly figure | boxplot with hover values of State, [min, lower fence, 25 percentile, median, 75 percentile, upper fence, max] 

    Errors
    -----------
    KeyError if data do not contain the correct columns
    """

    # Filter Data for States == Other
    data = data[data["state"] != "Other"]

    # Creating a list of states ordered by their median percentile value
    # to provide a left-to-right visual structure
    upper_q = list(data.groupby("state")[
                   "claim_amount"].median().sort_values(ascending=False).index)

    # Create traces for each state -> this was the only way I could get the whisker/plot scale correct
    traces = []
    for state in upper_q:
        state_data = data[data['state'] == state]
        trace = go.Box(
            y=state_data['claim_amount'],
            name=state,
            boxpoints='all',  # Show all points to maintain correct whisker length
            jitter=0.3,
            pointpos=-1.8,
            marker=dict(opacity=0),  # Make point markers invisible
            line=dict(width=2),
            boxmean=False  # Do not show mean
        )
        traces.append(trace)

    # Create the figure
    fig = go.Figure(data=traces)

    # Update layout
    fig.update_layout(
        title="Distribution of Car Accident Claims in Different States",
        yaxis=dict(
            title="Total Claim in USD"
        ),
        xaxis=dict(
            title="State"
        ),
        showlegend=False,
        template="plotly"
    )

    # Calculate IQR for each state to determine y-axis range
    iqr_ranges = data.groupby('state')['claim_amount'].apply(
        lambda x: (x.quantile(0.25), x.quantile(0.75)))
    iqr_min, iqr_max = iqr_ranges.apply(
        lambda x: x[0]).min(), iqr_ranges.apply(lambda x: x[1]).max()
    iqr = iqr_max - iqr_min

    # Update y-axis range to be slightly larger than the IQR range
    fig.update_yaxes(range=[-1000, iqr_max + 1.5 * iqr])

    return fig


# Gender Plots -----------------------------------------------------

def plotly_gender(data):
    """
    Function to generate a plotly figure of KDE distributions for Genders 
    compatible with Kaggle_medical_practice_20.csv and Insurance_claims_mendeleydata_6.csv

    Args
    -----------
    data: pd.DataFrame | data with columns: ["gender", "total_claim_amount"]

    Returns
    -----------
    plotly figure | kde plots overlaid with hover values of x coordinates (claim value)

    Errors
    -----------
    KeyError if data do not contain the correct columns
    """
    male_data = data.query("gender == 'Male'")['claim_amount']
    female_data = data.query("gender == 'Female'")['claim_amount']

    male_median_x = male_data.median().round(2)
    female_median_x = female_data.median().round(2)

    male_kde = ff.create_distplot([male_data], group_labels=[
                                  'Male'], show_hist=False, show_rug=False)
    female_kde = ff.create_distplot([female_data], group_labels=[
                                    'Female'], show_hist=False, show_rug=False)

    # Create the overlaid plot
    fig = go.Figure()

    # Male KDE Plot
    fig.add_trace(go.Scatter(x=male_kde['data'][0]['x'], y=male_kde['data'][0]['y'],
                             mode='lines', name='Male', fill='tozeroy', line=dict(color='blue'), opacity=0.1,
                             hoverinfo='x', xhoverformat="$,.2f", hovertemplate='Claim Amount: %{x:$,.2f}'))

    # Female KDE Plot
    fig.add_trace(go.Scatter(x=female_kde['data'][0]['x'], y=female_kde['data'][0]['y'],
                             mode='lines', name='Female', fill='tozeroy', line=dict(color='lightcoral'), opacity=0.1,
                             hoverinfo='x', xhoverformat="$,.2f", hovertemplate='Claim Amount: %{x:$,.2f}'))

    # Adding vertical lines for medians as scatter traces for legend
    male_median_y = max(male_kde['data'][0]['y'])
    female_median_y = max(female_kde['data'][0]['y'])

    fig.add_trace(go.Scatter(
        x=[male_median_x, male_median_x], y=[0, male_median_y],
        mode="lines",
        line=dict(color="lightblue", dash="dash"),
        name=f"Male Median ${male_median_x:,.0f}"
    ))

    fig.add_trace(go.Scatter(
        x=[female_median_x, female_median_x], y=[0, female_median_y],
        mode="lines",
        line=dict(color="lightpink", dash="dash"),
        name=f"Female Median ${female_median_x:,.0f}"
    ))

    # Update layout
    fig.update_layout(height=600,
                      title_text="Claim Distribution - Men vs Women: Higher Peaks Indicate More-Common Claim Amounts",
                      xaxis_title="Total Claim in USD",
                      yaxis_title="Density",
                      showlegend=True,
                      legend=dict(x=0.875, y=0.875))
    fig.update_yaxes(showticklabels=False)

    return fig


# fig.update_layout(yaxis=dict(tickformat='$,.2f'))

# def plotly_box_gender(data):
#     """
#     Function to generate a plotly figure of Boxplot distributions without outliers for Genders Across Insurance Types
#     compatible with Kaggle_medical_practice_20.csv

#     Args
#     -----------
#     data: pd.DataFrame | data with columns: ["gender", "total_claim_amount", "insurance"]

#     Returns
#     -----------
#     plotly figure | boxplot with hover values of State, then any of:
#     [max, upper fence, 75th percentile, median, 25th percentile, lower fence, min]

#     Errors
#     -----------
#     KeyError if data do not contain the correct columns
#     """

#     # Creating a list of states ordered by their median percentile value
#     # to provide a left-to-right visual structure
#     fig = px.box(data, x="insurance", y="claim_amount", color="gender")

#     # Update layout
#     fig.update_layout(
#         title="Distribution of Claims by Insurance Type for Men and Women",
#         yaxis=dict(
#             title="Total Claim in USD"
#         ),
#         xaxis=dict(
#             title="Insurance Type"
#         ),
#         showlegend=True,
#         template="plotly"
#     )

#     fig.update_layout(legend_title='Gender')

#     return fig

#     # Plot for different types of injuries from the Sample Data


def plotly_injury_bar(data, group, **kwargs):
    """
    Compatible with Sample Dataset, inverts x and y 
    """
    grouped = data.groupby(group)["claim_amount"].agg(["mean", "median"]).round(2).reset_index(
    ).sort_values(by="median", ascending=True).rename(columns={"mean": "Mean", "median": "Median"})
    fig = px.bar(data_frame=grouped, y=group, x=['Median', 'Mean'],
                 labels={'value': "Claim Value", group: group.replace(
                     "_", " ").title(), "variable": "Statistic"},
                 title=f'Mean and Median Claims by {group.replace("_", " ").title()}', barmode='group', **kwargs)
    # fig.update_layout(showlegend=True, width=1200, height=675)
    fig.update_layout(showlegend=True)
    fig.update_layout(xaxis=dict(tickformat='$,.2f'))

    return fig

    # Histplot function for injuries


# def plotly_injury_hist(data):
#     fig_h = px.histogram(data, x="claim_amount", nbins=25, labels={
#                          "claim_amount": "Claim", "value": "Count"})
#     fig_h.update_traces(hovertemplate='Claim: %{x}<br>Count: %{y}')
#     injury = data["Type of Injury"].unique()[0]
#     fig_h.update_layout(yaxis={
#                         "title": "Count"}, title=f"Histogram of Claim Distribution for {injury.title()}")
#     fig_h.update_traces(
#         name="Claims", marker_line_color='black', marker_line_width=1.5)
#     return fig_h

# Boxplot for injuries


# def plotly_boxplot_injury(data):
#     fig_b = px.box(data, x="claim_amount", labels={"claim_amount": "Claim"})
#     injury = data["Type of Injury"].unique()[0]
#     fig_b.update_layout(
#         title=f"Boxplot of Claim Distribution for {injury.title()}")

#     return fig_b

# AGE ------------------------


def plotly_age(data):
    age_data = data.dropna(subset="age")
    age_data["age"] = age_data["age"].astype("int8")
    age_data = age_data.sort_values(by="age", ascending=True)

    fig = px.line(age_data.groupby("age")["claim_amount"].agg(["median"])
                  .round(-2).reset_index(), x="age", y="median",
                  labels={"median": "Median Claim", "age": "Age"}, title="Median Claim Value by Age")
    fig.update_traces(name="Median Claim Value", showlegend=True)
    fig.update_layout(legend_title="")
    fig.update_layout(yaxis=dict(tickformat='$,.2f'))

    return fig


def plotly_age_hist(data, **kwargs):
    fig = px.histogram(data_frame=data["age"], labels={
                       "age": "Age"}, title="Number of Claims by Age", **kwargs)
    fig.update_layout(legend_title="", xaxis={"title": "Age"}, yaxis={
                      "title": "Number of Claims"}, showlegend=False)
    fig.update_traces(
        name="Claims", hovertemplate="Age %{x}<br> Number of Claims %{y}")
    fig.update_traces(name="Claims", marker_line_color='black',
                      marker_line_width=1.5)

    return fig


# def plotly_age_counts(data):
#     vcounts = data["age"].value_counts().sort_index()
#     fig = px.line(vcounts, labels={
#                   "age": "Age", "value": "Number of Claims"}, title="Total # of Claims by Age")
#     fig.update_layout(legend_title="")
#     fig.update_traces(name="Claims")

#     return fig


def plotly_age_bracket(data, **kwargs):
    group = data.groupby("age_bracket")["claim_amount"].agg(["median", "mean"]).round(-2).sort_index(ascending=False)\
        .rename(columns={"median": "Median", "mean": "Mean"})

    fig = px.bar(data_frame=group.reset_index(), y="age_bracket", x=["Median", "Mean"],
                 title="Mean and Median Claims by Age Bracket",
                 labels={"age_bracket": "Age Group",
                         "median": "Median", "mean": "Mean"},
                 barmode="group", **kwargs)

    fig.update_layout(legend_title_text="Statistic")
    fig.update_traces(hovertemplate="Claim Amount: %{x} <br>Age Group: %{y}")
    fig.update_layout(xaxis=dict(tickformat='$,.2f',
                      title="Claim Amount"), yaxis=dict(title="Age Group"))

    return fig


def plotly_age_line(data, group, **kwargs):
    grouped = data.groupby(group)["claim_amount"].agg(["median", "mean"]).round(-2).sort_index()\
        .rename(columns={"median": "Median", "mean": "Mean"}).reset_index()
    fig = px.line(data_frame=grouped, x=group, y=["Median", "Mean"],
                  title=f"Trends in Claim Values Across {group.replace('_', ' ').title()}",
                  labels=dict(group=group.replace("_", " ").title(), median="Median", mean="Mean"), markers=True, **kwargs)
    fig.update_layout(legend_title_text="Statistic")
    fig.update_traces(hovertemplate="Claim Amount: %{x} <br>Group: %{y}")
    fig.update_layout(yaxis=dict(tickformat='$,.2f', title="Claim Amount"), xaxis=dict(
        title=group.replace('_', ' ').title()))

    return fig


def plotly_scatter_age(data, group=None):
    fig = px.scatter(data, x="age", y="claim_amount", log_y=False, range_y=[0, data["claim_amount"].max()],
                     title="Claim Value vs Age (Zoom to Inspect, Click Legend to Activate/Deactivate Groups)",
                     color=group, symbol=group,
                     labels={group: group.replace("_", " ").title() if group else group,
                             "age": "Age", "claim_amount": "Claim Amount"})
    leg_title = group.replace('_', ' ').title() if group is not None else group
    fig.update_layout(xaxis={"title": "Age"}, yaxis={"title": "Claim Value"},
                      legend_title=f"{leg_title}")
    fig.update_layout(scattermode="group", scattergap=.75)
    fig.update_layout(yaxis=dict(tickformat='$,.2f'))

    return fig


def plotly_pie(data, column, **kwargs):
    fig = px.pie(data_frame=data, names=column, hole=.5,
                 title=f"Proportions Observed in the Data: {column.replace('_', ' ').title()}",
                 labels={column: column.replace('_', ' ').title()}, **kwargs)
    fig.update_layout(legend_title_text=f"{column.replace('_', ' ').title()}")
    # fig.update_traces(hovertemplate=f"Claim Amount %{y}<br> Statistic: %{x}<br>")
    return fig


# ----------------------- Mariam Functions -------------------------------
def plotly_mean_median_bar(data, group, **kwargs):  # KWARGS --------
    """
    Compatible with Most Datasets 
    """
    if "total_claim_amount" in data.columns:
        data = data.rename(columns={"total_claim_amount": "claim_amount"})
    grouped = data.groupby(group)["claim_amount"].agg(["mean", "median"]).round(2).reset_index(
    ).sort_values(by="median", ascending=True).rename(columns={"mean": "Mean", "median": "Median"})
    fig = px.bar(data_frame=grouped, x=group, y=['Median', 'Mean'],
                 labels={'value': "Claim Value", group: group.replace(
                     "_", " ").title(), "variable": "Statistic"},
                 title=f'Mean and Median Claims by {group.replace("_", " ").title()}', barmode='group',
                 color_continuous_scale="Viridis", **kwargs)  # KWARGS!!!!!!!!!!
    # fig.update_layout(showlegend=True, width=1200, height=675)
    fig.update_layout(showlegend=True)
    fig.update_layout(yaxis=dict(tickformat='$,.2f'))

    return fig


def plotly_filtered_claims(data, condition, **kwargs):
    fig = px.histogram(data_frame=data["claim_amount"], labels={"claim_amount": "Claim Value USD"},
                       title=f"Number of Claims by Value - {condition}", nbins=20, **kwargs)
    fig.update_layout(legend_title="", xaxis={"title": "Claim Value"}, yaxis={
                      "title": "Number of Claims"})
    fig.update_traces(name="Claims", marker_line_color='black', marker_line_width=1.5,
                      hovertemplate="Claim Value: %{x}<br> Number of Claims: %{y}")
    fig.update_layout(xaxis=dict(tickformat='$,.2f'), showlegend=False)
    return fig

# Boxplot for filtered data


def plotly_boxplot_filtered(data, condition, **kwargs):
    fig_b = px.box(data_frame=data, x="claim_amount", labels={
                   "claim_amount": "Claim"}, **kwargs)
    fig_b.update_layout(title=f"Boxplot of Claim Distribution for {condition}")
    fig_b.update_layout(xaxis=dict(tickformat='$,.2f'))

    return fig_b


def plotly_filtered_claims_bar(data, **kwargs):
    fig = px.bar(data_frame=data[data["Statistic"].isin(["Average Value", "Median Value"])],
                 x="Statistic", y=["Selected Data", "Excluded Data", "All Data"],
                 barmode="group",
                 title="Comparison of Average and Median Claim Values", **kwargs)

    fig.update_layout(legend_title="Dataset", yaxis={
                      "title": "Claim Value USD"}, bargap=.35)
    fig.update_traces(
        hovertemplate="Claim Amount %{y}<br> Statistic: %{x}<br>")
    fig.update_layout(yaxis=dict(tickformat='$,.2f'))

    return fig

# ---------------------------------------- display function ------------------------------------------------------------------


def display_analysis():

    # Car Insurance Data -----  ----------  -----------  --------------  -------------  ---------------  -------------------
    df_ins = pd.read_csv("data/Insurance_claims_mendeleydata_6.csv")

    # Process the insurance Data
    df_ins = preprocess_insurance_data(df_ins)

    st.header("**Analysis:**")
    graph_description = """
As you read through the analysis, we would also like you to be aware that these visualizations are interactive. 
Most of the plots will allow you to zoom in on a region by clicking and dragging over an area with your mouse. 
Also, if there is a legend in the upper-right of a visualization, you can click on an item in the legend to toggle that group on/off.
"""
    st.markdown(graph_description)

    # -------------------------------------------------------------------------------------------------
    # ------------------------ INSURANCE DATA ---------------------------------------------------------
    # elif data_source == "Auto Insurance Claims":
    data = df_ins
    st.subheader("This dataset is comprised of car accident claims.")
    st.write(
        "The dataset Insurance_claims_mendeleydata_6.csv contains insurance claims data recorded over a two-month period, from January 1, 2015, to March 1, 2015.")
    st.markdown("---")

    # Gender
    st.subheader("1. Gender:")

    gender_paragraph = """"Gender" refers to the policy holder (liable party) for this dataset. 
    The analysis of total claim amounts by gender reveals that 
    female policyholders tend to pay slightly larger claims compared to male policyholders.
The mean (average) claim amount for females is \$51,169, 
which is 3.94\% higher than the male mean of \$49,230.
The median, representing the middle value of all claims, 
is higher for females at \$57,120 compared to \$55,750 for males, showing a 2.46\% difference.
The mean provides an overall average but can be affected by extremely high or low claims.
The median offers a better sense of the typical claim amount.
Both metrics indicate that, on average, female policyholders report similar but mariginally higher claim amounts than their male counterparts.
"""

    st.markdown(gender_paragraph)

    st.plotly_chart(plotly_gender(data))

    # age_bracket
    st.subheader("2. Age:")

    age_paragraph = """
The ages in this dataset are confined to a fairly narrow range. 80\% of all claimants fall between
28-51 years old. As age increases, so does the average claim amount, with victims aged 60-65 having 
the highest average claims at \$58,900. Overall, there is a discernible upward trend in claim amounts with increasing age, 
underscoring a positive correlation between age and claim size. This likely indicates that older 
drivers tend to own more expensive cars, leading to higher claim settlements.
"""
# These findings highlight the significance of age as a determinant in assessing
# insurance claim risks and guiding strategic policy adjustments.

    st.markdown(age_paragraph)
    st.plotly_chart(plotly_age_hist(
        data, color_discrete_sequence=["sienna"]))
    st.plotly_chart(plotly_age_bracket(data, template="seaborn"))
    st.plotly_chart(plotly_age_line(
        data, "age_bracket", template="seaborn"))

    # Make of Car -> probably not that important
    st.subheader("3. Auto Manufacturer:")
    auto_paragraph = """
Nissan, Saab, and Subaru comprise the largest proportions of manufacturers in our data with 9\% each respectively.
Claims involving Ford vehicles have the highest median claim amount of around \$63,500 followed closely by
luxury brand BMW at \$62,480. The largest and smallest average claims for each manufacturer are separated by a range of 
around \$11,000 from the highest average, BMW at \$54,000 to the lowest average, Toyota, at \$43,000.

"""
    st.markdown(auto_paragraph)

    # Treemap
    fig = px.treemap(data[["auto_make", "auto_model"]].value_counts(normalize=True).round(2).reset_index(),
                     path=["auto_make", "auto_model"], values="proportion", title="Distribution of Makes and Models")

    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    fig.update_traces(
        hovertemplate="Vehicle %{label}<br>Percentage of Records %{value:.1%}")
    st.plotly_chart(fig)

    st.plotly_chart(plotly_injury_bar(data, "auto_make"))

    st.plotly_chart(plotly_injury_bar(data, "auto_model"))

    # auto_year -> CURIOUS DATA, implies older cars are of a higher claim value
    st.subheader("4. Model year:")
    model_year_paragraph = """The analysis of auto year and claim amounts for this dataset indicate
        older model years tend to receive higher average and median claim amounts compared to newer models.
For example, vehicles from the mid-to-late 1990s and early 2000s (e.g., 1995-2005) show higher average claim amounts, 
ranging from \$47,134 to \$57,535. This suggests potentially higher repair costs or difficult-to-locate parts,
and perhaps more adverse outcomes due to deteriorating safety features within the vehicle.
In contrast, newer model years from 2010 onwards (e.g., 2010-2015) demonstrate lower average claim amounts,
ranging from \$42,853 to \$48,323, likely indicating improved vehicle safety and durability standards.

"""
    st.markdown(model_year_paragraph)
    st.plotly_chart(plotly_mean_median_bar(data, "auto_year", template="presentation")
                    .update_layout(xaxis=dict(tickvals=np.arange(1995, 2016))))
    st.plotly_chart(plotly_age_line(
        data, "auto_year", template="presentation"))

    # States
    state1, state2 = st.columns([2, 2])
    with state1:
        st.subheader("5. State:")

        state_paragraph = """
        New York (NY) makes up the largest proportion of claims in our data, and it also has the largest
        mean and median claim values at roughly \$54,250 and \$58,675 respectively. With the exception of 
        Ohio, all the states represented in our data are on the east coast. Ohio has the smallest average and median claims
        of all the states present while also representing the fewest claims in the data.
"""
        st.markdown(state_paragraph)
    with state2:
        st.plotly_chart(plotly_pie(data, "state", template="presentation"))
    st.plotly_chart(plotly_states(data))
    # st.plotly_chart(plotly_box_states(data)) # Removed to avoid over complication

    # Incident Date showed a relatively stationary time series, not a lot of inferential value

    # accident_type
    acc1, acc2 = st.columns([2, 2])
    with acc1:
        st.subheader("6. Accident Type:")

        accident_paragraph = """
        Claims involving moving vehicles (single or multi-vehicle) have similarly sized claim values, 
        whereas claims for unattended vehicles typically have much smaller claim values. This disparity can be explained by the absence of 
        physical injuries for claims involving vehicle theft or damage to a parked car.  
        Multi-vehicle and single-vehicle collisions average roughly \$62,000 and \$63,500 respectively per claim.
Parked car and vehicle theft incidents have notably lower average claim amounts at \$5,300 and \$5,500.

"""
        st.markdown(accident_paragraph)

    with acc2:
        st.plotly_chart(plotly_pie(
            data, "accident_type", template="presentation"))
    st.plotly_chart(plotly_mean_median_bar(
        data, "accident_type", template="seaborn"))

    # collision_type
    coll1, coll2 = st.columns([2, 2])
    with coll1:
        st.subheader("7. Collision Type:")

        collision_paragraph = """Front collisions account for 24.4\% of all claims, with an average payout of \$64,777 and 
        a median of \$63,950. This makes logical sense, as front-end collisions will endanger the driver, any other front-seat
        occupants, and the components of the engine. Side and rear collisions receive incrementally smaller claim sizes, and as 
previously described, unattended vehicle claims receive substantially less.
"""
        st.markdown(collision_paragraph)

    with coll2:
        st.plotly_chart(plotly_pie(
            data, "collision_type", template="presentation"))
    st.plotly_chart(plotly_mean_median_bar(data, "collision_type"))

    # incident_severity
    serv1, serv2 = st.columns([2, 2])
    with serv1:
        st.subheader("8. Incident Severity:")

        severity_paragraph = """The two most frequent incident severities found in this data are minor damage, representing 42\% of all claims,
        and total losses representing 32.4\% of all claims. Major Damage incidents have the highest average claim amount at almost \$64,000,
Total losses follow closely behind with an average claim value of \$61,792. Total losses having lower claim amounts than major damage
is most likely attributed to insurers wanting to save costs on mechanical labor and parts. Often, insurance companies will prefer to 
"total out" a car rather than repair it if the estimated repair costs are larger than the appraised value of a car. 
Minor Damage claims average \$48,600, well below the previous 2 categories. Trivial Damage claims receive significantly 
smaller compensation at \$5,300 on average. 
"""
        st.markdown(severity_paragraph)

    with serv2:
        st.plotly_chart(plotly_pie(
            data, "incident_severity", template="presentation"))
    st.plotly_chart(plotly_mean_median_bar(
        data, "incident_severity", template="seaborn"))

    # bodily_injuries
    injury1, injury2 = st.columns([2, 2])
    with injury1:
        st.subheader("9. Number of Bodily Injuries:")

        bodily_injuries_paragraph = """This data has a balanced proportion of claims with 0, 1, and 2 bodily injuries.
        Claims without bodily injuries have a median value of \$56,700, 
        while those with one injury surprisingly have a slightly lower median value of \$54,000. Claims involving 
        two injuries have the largest median value of \$57,935 as expected. 
"""
        st.markdown(bodily_injuries_paragraph)

    with injury2:
        st.plotly_chart(plotly_pie(
            data, "bodily_injuries", template="presentation"))
    st.plotly_chart(plotly_mean_median_bar(
        data, "bodily_injuries", color_discrete_sequence=["chocolate", "gray"]))

    # authorities_contacted
    author1, author2 = st.columns([2, 2])
    with author1:
        st.subheader("10. Authorities Contacted:")

        authorities_paragraph = """There are 4 distinct categories of authorities listed in our data:
        Fire, Ambulance, Police, and "Other". For the specifically named authorities, cases involving the fire department 
        received the largest claims. They have an average claim amount of about \$61,439 and a median value of \$60,000. 
        Next largest, incidents where an ambulance was contacted have an average claim amount of approximately 
        \$60,357, with a median value of \$59,300. Third, incidents requiring police intervention have a lower mean claim amount of roughly \$44,193, 
with a median of \$51,800.  "Other" authorities had the largest average claim amount of around \$65,156 
and a median value of \$64,080. While police do address issues that result in large claims, they seem to
handle the overwhelming majority of small claim instances. Notice how *only police* handle claims with values
less than \$18,s
"""
        st.markdown(authorities_paragraph)

    with author2:
        st.plotly_chart(plotly_pie(data.dropna(
            subset="authorities_contacted"), "authorities_contacted", template="presentation"))
        # st.plotly_chart(plotly_pie(
        #     data, "authorities_contacted", template="presentation"))
    st.plotly_chart(plotly_mean_median_bar(
        data, "authorities_contacted", template="plotly"))
    st.plotly_chart(plotly_scatter_age(data, "authorities_contacted"))

    # police_report_available
    pol1, pol2 = st.columns([2, 2])
    with pol1:
        st.subheader("11. Police Report:")

        police_report_paragraph = """Incidents with a police report available had an average claim amount of 
        \$52,083, which is approximately 11.5\% higher than incidents without a report (\$46,738).
The median claim amount for incidents with a police report was \$57,110, showing a difference of about 
3\% lower compared to incidents without a report (\$55,500).
Cases where the availability of a police report was unknown showed a mean claim amount of 
\$52,171 and a median of \$58,050.

"""
        st.markdown(police_report_paragraph)

    with pol2:
        st.plotly_chart(plotly_pie(
            data, "police_report_available", template="presentation"))
    st.plotly_chart(plotly_mean_median_bar(
        data, "police_report_available", color_discrete_sequence=["blue", "lightgrey"]))

    # --------------------------------- Filtering Conditions -------------------------------------------

    st.header("Try Out Multiple Filters:")
    st.write('If you would like to deactivate a filter select: "None"')

    # Age -------
    min_age, max_age = st.slider("Age Range", min_value=data["age"].min().astype(int), max_value=data["age"].max().astype(int),
                                 value=(data["age"].min().astype(int), data["age"].max().astype(int)), step=1)

    # Boolean Mask for the Filter
    age_condition = (data["age"] >= min_age) & (data["age"] <= max_age)

    col1, col2 = st.columns(2)

    # gender -----------
    with col1:
        gender_type_status = st.selectbox(
            "Gender:", [None] + list(data["gender"].unique()), index=0)
        if gender_type_status:
            gender_type_condition = (data["gender"] == gender_type_status)
        else:
            gender_type_condition = True

    # accident_type -----------
    with col2:
        accident_type_type_status = st.selectbox(
            "Accident Type:", [None] + list(data["accident_type"].unique()), index=0)
        if accident_type_type_status:
            accident_type_condition = (
                data["accident_type"] == accident_type_type_status)
        else:
            accident_type_condition = True

    col3, col4 = st.columns(2)

    # collision_type -----------
    with col3:
        collision_type_status = st.selectbox(
            "Collision Type:", [None] + list(data["collision_type"].unique()), index=0)
        if collision_type_status:
            collision_type_condition = (
                data["collision_type"] == collision_type_status)
        else:
            collision_type_condition = True

    # incident_severity -----------
    with col4:
        incident_severity_type_status = st.selectbox(
            "Incident Severity:", [None] + list(data["incident_severity"].unique()), index=0)
        if incident_severity_type_status:
            incident_severity_type_condition = (
                data["incident_severity"] == incident_severity_type_status)
        else:
            incident_severity_type_condition = True

    col5, col6 = st.columns(2)

    # authorities_contacted -----------
    with col5:
        authorities_contacted_type_status = st.selectbox("Authorities Contacted:", [None] +
                                                         list(data["authorities_contacted"].dropna().unique()), index=0)
        if authorities_contacted_type_status:
            authorities_contacted_condition = (
                data["authorities_contacted"] == authorities_contacted_type_status)
        else:
            authorities_contacted_condition = True

    # state -----------
    with col6:
        state_type_status = st.selectbox(
            "State:", [None] + list(data["state"].unique()), index=0)
        if state_type_status:
            state_condition = (data["state"] == state_type_status)
        else:
            state_condition = True

    col7, col8 = st.columns(2)

    # property_damage -----------
    with col7:
        property_damage_type_status = st.selectbox(
            "Property Damage:", [None] + list(data["property_damage"].unique()), index=0)
        if property_damage_type_status:
            property_damage_condition = (
                data["property_damage"] == property_damage_type_status)
        else:
            property_damage_condition = True

    # bodily_injuries -----------
    with col8:
        bodily_injuries_type_status = st.selectbox("Number of Bodily Injuries:", [
            None] + list(data["bodily_injuries"].unique()), index=0)
        if bodily_injuries_type_status:
            bodily_injuries_condition = (
                data["bodily_injuries"] == bodily_injuries_type_status)
        else:
            bodily_injuries_condition = True

    col9, col10 = st.columns(2)

    # police_report_available -----------
    with col9:
        police_report_available_type_status = st.selectbox("Police Report Available?:", [
            None] + list(data["police_report_available"].unique()), index=0)
        if police_report_available_type_status:
            police_report_available_condition = (
                data["police_report_available"] == police_report_available_type_status)
        else:
            police_report_available_condition = True

    # auto_make -----------
    with col10:
        auto_make_type_status = st.selectbox(
            "Auto Make:", [None] + list(data["auto_make"].unique()), index=0)
        if auto_make_type_status:
            auto_make_condition = (
                data["auto_make"] == auto_make_type_status)
        else:
            auto_make_condition = True

    col11, col12 = st.columns(2)

    # auto_model -----------
    with col11:
        auto_model_type_status = st.selectbox(
            "Auto Model:", [None] + list(data["auto_model"].unique()), index=0)
        if auto_model_type_status:
            auto_model_condition = (
                data["auto_model"] == auto_model_type_status)
        else:
            auto_model_condition = True

    # auto_year -----------
    with col12:
        auto_year_type_status = st.selectbox("Auto Year:", [
            None] + list(data["auto_year"].sort_values(ascending=False).unique()), index=0)
        if auto_year_type_status:
            auto_year_condition = (
                data["auto_year"] == auto_year_type_status)
        else:
            auto_year_condition = True

    # COLLECTING CONDITIONS  -----------------------------------------------------
    all_conditions = age_condition & gender_type_condition & accident_type_condition\
        & collision_type_condition & incident_severity_type_condition & authorities_contacted_condition\
        & state_condition & property_damage_condition & bodily_injuries_condition & police_report_available_condition\
        & auto_make_condition & auto_model_condition & auto_year_condition

    st.markdown("---")

    st.subheader("Here's a breakdown of the data you have selected:")

    # SUMMARY PLOTS
    # DF for comparison of numeric profiles
    description_table = pd.DataFrame(data[all_conditions]["claim_amount"].describe().round(2)).reset_index()\
        .merge(pd.DataFrame(data[~all_conditions]["claim_amount"].describe()).reset_index()
               .rename(columns={"claim_amount": "Excluded Data"})
               .round(2)).reset_index()\
        .rename(columns={
            "claim_amount": "Selected Data",
            "index": "Statistic"}).drop(columns="level_0")

    # DF of all rows description
    describe_df = pd.DataFrame()
    describe_df["Statistic"] = description_table["Statistic"].copy()
    describe_df["All Data"] = data["claim_amount"].describe().values.round(2)

    # Merge 3rd df
    description_table = description_table.merge(
        describe_df, on="Statistic")

    # Mapping the statistic values
    description_table["Statistic"] = description_table["Statistic"].map({"count": "Number of Rows",
                                                                         "mean": "Average Value",
                                                                         "std": "Standard Deviation",
                                                                         "min": "Minimum Value",
                                                                         "25%": "25th Percentile Value",
                                                                         "50%": "Median Value",
                                                                         "75%": "75th Percentile Value",
                                                                         "max": "Maximum Value"})

    description_table.drop(2, inplace=True)
    description_table = description_table.iloc[[0, 2, 3, 4, 1, 5, 6], :]

    # Sample size warning
    if data[all_conditions].shape[0] <= 10:
        st.write(
            "This is a small subset of data, so use discretion when interpretting the results.")

    # Display the dataframe
    st.dataframe(description_table,
                 use_container_width=True, hide_index=True)

    # Only display distribution plots if there are 10 or more observations
    if data[all_conditions].shape[0] >= 10:
        distribution_skew_condition = (data[all_conditions]["claim_amount"].max() - data[all_conditions]["claim_amount"].quantile(.9)) >\
            (data[all_conditions]["claim_amount"].quantile(.9) -
                data[all_conditions]["claim_amount"].quantile(.75))

        # Account for extreme outliers
        if distribution_skew_condition:
            hist_data = data[all_conditions][data[all_conditions]["claim_amount"]
                                             < data[all_conditions]["claim_amount"].quantile(.9)]

            condition = "Selected Data without Extreme Outliers"
            # Histogram
            st.plotly_chart(plotly_filtered_claims(hist_data, condition))
            # Boxplot
            st.plotly_chart(plotly_boxplot_filtered(hist_data, condition))

        else:  # If not distribution_skew_condition
            condition = "Selected Data"
            st.plotly_chart(plotly_filtered_claims(
                data[all_conditions], condition))
            # Boxplot
            st.plotly_chart(plotly_boxplot_filtered(
                data[all_conditions], condition))

    # Comparison Bar Plot
    st.plotly_chart(plotly_filtered_claims_bar(
        description_table, template="plotly_white"))

    # Scatterplot of Claim vs Age
    keys = [None] + list(data.select_dtypes(
        exclude=np.number).columns.str.title().sort_values().str.replace("_", " "))
    values = [
        None] + sorted(list(data.select_dtypes(exclude=np.number).columns), key=lambda x: x.lower())
    age_col_dict = dict(zip(keys, values))

    st.subheader("Use the Scatterplot to Explore Groups from the Data")
    group = st.selectbox("Select Subsets of the Data:", keys)
    st.plotly_chart(plotly_scatter_age(
        data[all_conditions], age_col_dict[group]))

    # -------------------------------- Summary with Filters -----------------------------------


if __name__ == "__main__":
    display_analysis()
