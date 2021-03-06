import pandas as pd
import numpy as np
import re
import pdb

def add_claim_resolution_cols(df):
  new_cols=['Final_disposition', 'Final_disposition_Date', 
  'Days_Accid_Final', 'Days_Assemb_Final']
  orig_cols=df.columns.tolist()
  cols=orig_cols+new_cols
  disp_df = df.reindex(columns=cols)
  return disp_df

def combine_disp_cols(df, disp_date, disp_name):
  select_df = df[df[disp_date].notnull()]
  select_df['Final_disposition_Date']=select_df[disp_date]
  select_df['Final_disposition']=disp_name
  return select_df

def add_disposition_labels(df):
  final_disps = [('PPD Non-Scheduled Loss Date','PPD'),('PPD Scheduled Loss Date',
   'SLU'),('Section 32 Date', 'S32'),('PTD Date', 'PTD')]
  additional_dfs = [combine_disp_cols(df, disp_date, disp_name) for disp_date,disp_name in final_disps]
  return pd.concat(additional_dfs,ignore_index=True,axis=0)

def coerce_cols_to_datetime(df):
  dates=[name for name in df.columns if 'Date' in name]
  days = [name for name in df.columns if 'Days' in name]
  date_names = dates+days
  df[date_names]=df[date_names].apply(pd.to_datetime,errors='coerce')
  return df

def missing_accid_date(df):
  select_df = df[df['Accident Date'].isnull()]
  select_df['Accident Date']=select_df['Assembly Date']
  return select_df

def replace_missing_accid_date(df):
  fill_dateDF = missing_accid_date(df)
  drop_nullidx = df[df['Accident Date'].isnull()].index
  drop_nullDF = df.drop(drop_nullidx)
  return  pd.concat([fill_dateDF,drop_nullDF],ignore_index=True,axis=0)

def days_diff_datetime_cols(df):
  replace_df = replace_missing_accid_date(df)  
  replace_df['Days_Accid_Final']=(replace_df['Final_disposition_Date']-replace_df['Accident Date']).dt.days
  replace_df['Days_Assemb_Final']=(replace_df['Final_disposition_Date']-replace_df['Assembly Date']).dt.days
  return replace_df

def drop_unneccessary_cols(df):
  unneed_cols= ['Claim Identifier', 'Section 32 Date','PPD Scheduled Loss Date','PPD Non-Scheduled Loss Date',
                'PTD Date','Medical Fee Region']
  desc_cols = [name for name in df.columns if 'Description' in name]
  drop_cols = unneed_cols + desc_cols
  scoped_df= df.drop(columns=drop_cols,axis=1)
  return scoped_df

def strip_char(col):
  clean = col.str.replace(r"([*,-])",'')
  return clean

def remove_asterisks_commas(df):
  cols= ['OIICS Part Of Body Code','OIICS Nature of Injury Code',
  'OIICS Injury Source Code','OIICS Event Exposure Code',
                   'OIICS Secondary Source Code']
  df[cols] = df[cols].apply(strip_char).astype('float')
  return df

def clean_coerce_tonum(df,cols):
  return df[cols].apply(strip_char).apply(clean_zip)

def clean_cols(df):
  cols = ['Average Weekly Wage','Zip Code', 
  'Interval Assembled to ANCR']
  oiic_df = remove_asterisks_commas(df)
  df[cols] = clean_coerce_tonum(oiic_df,cols)
  return df

def clean_zip(col):
  return pd.to_numeric(col, errors='coerce',downcast='signed')
 
def split_datecol(df,datecol):
  df[f'{datecol}_month']= df[f'{datecol}'].dt.month
  df[f'{datecol}_day']= df[f'{datecol}'].dt.day
  df[f'{datecol}_year']= df[f'{datecol}'].dt.year
  return pd.concat([df[f'{datecol}_month'],df[f'{datecol}_day'],df[f'{datecol}_year']], axis=1)

def split_datetime_df(df):
  datetime_cols = df.select_dtypes(include='datetime').columns
  splitdates_list = [split_datecol(df,col) for col in datetime_cols]
  return pd.concat(splitdates_list, axis=1).fillna(0)

def transform_obj(df):
  obj_df = df.select_dtypes(include='object')
  objcols = obj_df.columns.tolist() #set(list(obj_df.columns))
  objcols.remove('Final_disposition')
  stepcols = [([col], [MultiLabelBinarizer()]) for col in objcols]
  steps = [(['Final_disposition'],LabelEncoder())]+stepcols
  obj_mapper = DataFrameMapper(steps, default = None, df_out = True)
  return obj_mapper.fit_transform(obj_df)

def transform_num(df):
  num_df = df.select_dtypes(exclude= ['object', 'datetime']).fillna(0)
  numcols = num_df.columns.tolist()
  numsteps = [([col],SimpleImputer(strategy='most_frequent')) for col in numcols]
  num_mapper =  DataFrameMapper(numsteps, input_df=True, df_out=True)
  return num_mapper.fit_transform(num_df)

def tranform_df(df):
  split_datedf = split_datetime_df(df)
  transformed_obj = transform_obj(df)
  transformed_num = transform_num(df)
  return pd.concat([transformed_num, transformed_obj, split_datedf],axis=1).sample(frac=1).reset_index(drop=True)
# # remove comma and replace Nan values with zero and cast as new datatype
# def type_col(df,col,typecast):
#     df[col]=df[col].str.replace(',', '').replace('-','').replace(np.NaN,0).replace([None],0).astype(typecast)
#     return df
# # get index of rows where column value is not a digit and replace with another value
# def not_num_replace(df,col,replaceval=int):
#   zip_str_idx = df[~(df[col].str.isdigit())].index
#   df.loc[zip_str_idx,[col]]=replaceval
#   return df

#   # removes commas and dashes, replaces None with 0, especially for AWW column
# def type_col(df,col,typecast):
#   df[col]=df[col].str.replace(',', '').replace('-','').replace([None],0).astype(typecast)
#   return df

  
  