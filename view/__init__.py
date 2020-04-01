#  format transformation
def preprocess_data(df):
    def is_digit(val):
        if val:
            try:
                float(val)
                return True
            except:
                return False
        else:
            return False

    is_digit_udf=udf(is_digit,BooleanType())
    return df.withColumn("timestamp",unix_timestamp("timestamp",'MM/dd/yyyy HH:mm').cast('integer')) \
        .withColumn("readtime_existent",col("timestamp"))


# expand data set with 60s interval
def Resampling(df_out):
    # define function to create date range
    def date_range(t1,t2,step=60):
        """Returns a list of equally spaced points between t1 and t2 with stepsize step."""
        return [t1 + step * x for x in range(int((t2 - t1) / step) + 1)]

    # define udf
    date_range_udf=func.udf(date_range,ArrayType(LongType()))

    df_base= \
        df_out.groupBy('device_name','hour','mac_address','division','serial_number','econet_object_name',
                       'software_version') \
            .agg(func.min('timestamp').cast('integer').alias('timestamp_min'),
                 func.max('timestamp').cast('integer').alias('timestamp_max')) \
            .withColumn("timestamp",func.explode(date_range_udf("timestamp_min","timestamp_max"))) \
            .drop('timestamp_min','timestamp_max')

    # left outer join existing read values
    ans=df_base.join(df_out,['device_name','hour','mac_address','division','serial_number','software_version',
                             'econet_object_name','timestamp'],"outer")
    df_base=df_base.drop('econet_object_value')
    return df_base,ans

def Resampling(df_out):
    # define function to create date range
    def date_range(t1,t2,step=60):
        """Returns a list of equally spaced points between t1 and t2 with stepsize step."""
        return [t1 + step * x for x in range(int((t2 - t1) / step) + 1)]

    # define udf
    date_range_udf=func.udf(date_range,ArrayType(LongType()))

    df_base= \
        df_out.groupBy('device_name','hour','mac_address','division','serial_number','econet_object_name',
                       'software_version') \
            .agg(func.min('timestamp').cast('integer').alias('timestamp_min'),
                 func.max('timestamp').cast('integer').alias('timestamp_max')) \
            .withColumn("timestamp",func.explode(date_range_udf("timestamp_min","timestamp_max"))) \
            .drop('timestamp_min','timestamp_max')

    # left outer join existing read values
    return df_base.join(df_out,['device_name','hour','mac_address','division','serial_number','software_version',
                                'econet_object_name','timestamp'],"leftouter")
# Forward-fill and Backward-fill Using Window Functions
def fill(df_all_dates):
    window_ff=Window.partitionBy('device_name','hour','mac_address','division','serial_number','econet_object_name',
                                 'software_version') \
        .orderBy('timestamp') \
        .rowsBetween(-sys.maxsize,0)

    window_bf=Window.partitionBy('device_name','hour','mac_address','division','serial_number','econet_object_name',
                                 'software_version') \
        .orderBy('timestamp') \
        .rowsBetween(0,sys.maxsize)

    # create the series containing the filled values
    read_last=func.last(df_all_dates['econet_object_value'],ignorenulls = True).over(window_ff)
    readtime_last=func.last(df_all_dates['readtime_existent'],ignorenulls = True).over(window_ff)

    read_next=func.first(df_all_dates['econet_object_value'],ignorenulls = True).over(window_bf)
    readtime_next=func.first(df_all_dates['readtime_existent'],ignorenulls = True).over(window_bf)

    # add the columns to the dataframe
    return df_all_dates.withColumn('readvalue_ff',read_last) \
        .withColumn('readtime_ff',readtime_last) \
        .withColumn('readvalue_bf',read_next) \
        .withColumn('readtime_bf',readtime_next)


# define interpolation function
linear_interpolation_list=['ambientt','disctemp','evaptemp','exactual','hrs_comp',"hrshifan",
                           'hrslofan','hrslohtr','hrsuphtr','i_rmsval','lohtrtmp','powrwatt',
                           'seccount','suctiont','totalkwh','uphtrtmp','wfsignal']
linear_interpolation_list=[e.upper() for e in linear_interpolation_list]


def execute_interpolation(df_filled):
    # define interpolation function
    def interpol(x,x_prev,x_next,y_prev,y_next,y,name):
        y_interpol=y
        if name not in linear_interpolation_list:
            y_interpol=y_prev
        else:
            try:
                x,x_prev,x_next,y_prev,y_next=float(x),float(x_prev),float(x_next),float(y_prev),float(y_next)
                if x_prev == x_next:
                    y_interpol=y
                else:
                    m=(y_next - y_prev) / (x_next - x_prev)
                    y_interpol=y_prev + m * (x - x_prev)
            except Exception as e:
                y_interpol=y
        return str(y_interpol)

    # convert function to udf
    interpol_udf=func.udf(interpol,StringType())

    # add interpolated columns to dataframe and clean up
    df_filled=df_filled.withColumn('readvalue_interpol',
                                   interpol_udf('timestamp','readtime_ff','readtime_bf','readvalue_ff','readvalue_bf',
                                                'econet_object_value','econet_object_name')) \
        .drop('readtime_existent','readtime_ff','readtime_bf','readvalue_bf','readvalue_bf','readvalue_ff') \
        .withColumnRenamed('reads_all','econet_object_value') \
        # .withColumn('timestamp', func.from_unixtime(col('timestamp')))

    return df_filled


'''
.withColumn("econet_object_value", col("readvalue_interpol"))\
                .withColumn("timestamp", to_timestamp("timestamp", 'yyyy-MM-dd HH:mm'))\
                .drop('readvalue_interpol')
'''


def combine(df,df_base):
    df=df.withColumn("econet_object_value",col("readvalue_interpol")) \
        .drop('readvalue_interpol')

    return df_base.join(df,['device_name','hour','mac_address','division','serial_number','software_version',
                            'econet_object_name','timestamp'],"leftouter") \
        .withColumn('timestamp',func.from_unixtime(col('timestamp'))) \
        .withColumn("timestamp",to_timestamp("timestamp",'yyyy-MM-dd HH:mm'))


def interpolation(path):
    df=spark.read.parquet(path)
    df_=preprocess_data(df)
    df_base,df=Resampling(df)
    df=fill(df)
    df=execute_interpolation(df)
    df=combine(df,df_base)

    return df

# convert function to udf
# interpol_udf = func.udf(interpol, StringType())

# # add interpolated columns to dataframe and clean up
# df_filled = df_filled.withColumn('readvalue_interpol', interpol_udf('timestamp', 'readtime_ff', 'readtime_bf', 'readvalue_ff', 'readvalue_bf', 'econet_object_value', 'econet_object_name'))\
#                     .drop('readtime_existent', 'readtime_ff', 'readtime_bf', 'readvalue_bf', 'readvalue_bf','readvalue_ff')\
#                     .withColumnRenamed('reads_all', 'econet_object_value')\
#                     .withColumn('timestamp', func.from_unixtime(col('timestamp')))


