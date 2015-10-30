# Scroll down the the section marked MAIN

# Imports for loading Data
import numpy as np
import scipy.io as sio
import csv
import os
import h5py
import cPickle as pickle
import gzip

# Import the methods for 2-pt stats
from pymks import PrimitiveBasis
from pymks.stats import correlate
from pymks.tools import draw_correlations
from pymks.tools import draw_microstructures
from pymks import MKSHomogenizationModel
from pymks.tools import draw_component_variance
from pymks.tools import draw_components
from pymks.tools import draw_gridscores_matrix

from sklearn.cross_validation import train_test_split, cross_val_score
from sklearn.decomposition import PCA
from sklearn import linear_model
from sklearn.cross_validation import LeaveOneOut
from sklearn.grid_search import GridSearchCV
from sklearn import svm, tree
from sklearn.preprocessing import StandardScaler


# Just loads the data from the .mat file in dropbox
def load_data(filename):    
  data = sio.loadmat(filename)
  # The line below is because the matlab format has to be "unstructed"
  #print data['phase_field_solid']
  return shuffle_ndarray(data['phase_field_model'])


# The pymks takes a different format of data than our .mat data
def shuffle_ndarray(data):
  n,m,k = data.shape
  new_data = np.zeros((k,n,m))
  for i in xrange(k):
    new_data[i, :, :] = data[:, :, i]
  return new_data


# Opens the metadata csv in data/metadata.csv, necessary for reading %Ag, %Cu, v etc..
def load_metadata(filename):
  metadata = []
  with open(filename, 'rb') as csvfile:
    metareader = csv.reader(csvfile, delimiter='\t', quotechar='|')
    next(metareader, None)
    for row in metareader:
      if float(row[2]) > .2: continue
      metadata.append({'ag':float(row[0]),
                       'cu':float(row[1]),
                       'sv':float(row[2]), 
                       'x':int(row[3]), 
                       'y':int(row[4]), 
                       'filename':row[5]+'.mat'})
  return metadata


# Extracts the "best slice" of the block,
# Currently takes the slice 10th from the end
def get_best_slice(al_data_slice):
  # TODO come up with a better way to summarize the block
  return al_data_slice[-10:-9]


def plot_component_variance(x, y):
  prim_basis = PrimitiveBasis(n_states=3, domain=[0, 2])
  model = MKSHomogenizationModel(basis=prim_basis)
  model.n_components = 20
  model.fit(x, y, periodic_axes=[0, 1]) 
  # Draw the plot containing the PCA variance accumulation
  draw_component_variance(model.dimension_reducer.explained_variance_ratio_)

def run_conventional_linkage(x, y, n_comps, linker_model, verbose=2):
  loo_cv = LeaveOneOut(x.shape[0])
  print "--->Cross validating"
  cvs = cross_val_score(linker_model, x, y, cv=5, scoring='r2', verbose=verbose)  
  mse = cross_val_score(linker_model, x, y, cv=5, scoring='mean_squared_error', verbose=verbose)  
  print np.mean(cvs), np.mean(mse)
  return np.mean(cvs), np.std(cvs), np.mean(mse), np.std(mse)

def plot_components(x, y, n_comps, linker_model, verbose=2):
  prim_basis = PrimitiveBasis(n_states=3, domain=[0, 2])
  model = MKSHomogenizationModel(basis=prim_basis,
                                 property_linker=linker_model)
  model.n_components = 5
  model.fit(x,y,periodic_axes=[0,1])

  print model.property_linker.coef_
  draw_components([model.reduced_fit_data[0:3, :2], 
                   model.reduced_fit_data[3:6, :2],
                   model.reduced_fit_data[6:9, :2],
                   model.reduced_fit_data[9:11, :2], 
                   model.reduced_fit_data[11:14, :2],
                   model.reduced_fit_data[14:16, :2],
                   model.reduced_fit_data[16:17, :2],
                   model.reduced_fit_data[17:18, :2]],
                   ['Ag:0.237	Cu:0.141	v:0.0525', 
                    'Ag:0.237	Cu:0.141	v:0.0593', 
                    'Ag:0.237	Cu:0.141	v:0.0773',
                    'Ag:0.237	Cu:0.141	v:0.0844', 
                    'Ag:0.239	Cu:0.138	v:0.0791', 
                    'Ag:0.239	Cu:0.138	v:0.0525', 
                    'Ag:0.237	Cu:0.141	v:0.0914', 
                    'Ag:0.237	Cu:0.141	v:0.0512']) 


def run_gridcv_linkage(x, y):


  X_train, X_test, y_train, y_test = train_test_split(x.reshape(flat_shape), y,
                                                    test_size=0.1, random_state=0)
  print 'Training set size: ', (X_train.shape)
  print 'Testing set size: ', (X_test.shape)

 #params_to_tune = {'degree': np.arange(1, 4), 'n_components': np.arange(1, 8)}
  params_to_tune = {'degree': np.arange(1, 2), 'n_components': np.arange(3, 5)}
  fit_params = {'size': x[0].shape, 'periodic_axes': [0, 1]}
  loo_cv = LeaveOneOut(X_train.shape[0])
  gs = GridSearchCV(model, params_to_tune, cv=loo_cv, n_jobs=-1, fit_params=fit_params, scoring='mean_squared_error').fit(X_train, y_train)
  print('Order of Polynomial'), (gs.best_estimator_.degree)
  print('Number of Components'), (gs.best_estimator_.n_components)
  print('R-squared Value'), (gs.score(X_test, y_test))
  
  #draw_gridscores_matrix(gs, ['n_components', 'degree'], score_label='R-Squared',
  #                     param_labels=['Number of Components', 'Order of Polynomial'])

def compute_correlations(x):
  print "-->Constructing Correlations"
  prim_basis = PrimitiveBasis(n_states=3, domain=[0,2])
  x_ = prim_basis.discretize(x)
  x_corr = correlate(x_, periodic_axes=[0, 1])
  x_corr_flat = np.ndarray(shape=(x.shape[0],  x_corr.shape[1]*x_corr.shape[2]*x_corr.shape[3]))
  row_ctr = 0
  for row in x_corr:
    x_corr_flat[row_ctr] = row.flatten()
    row_ctr += 1
  return x_corr, x_corr_flat

def compute_pca_scores(x_flat):
  pca = PCA(n_components=5)
  x_pca = pca.fit(x_flat).transform(x_flat)
  return x_pca


  #~~~~~~~MAIN~~~~~~~
if __name__ == '__main__':
  
  if os.path.isfile('cache/x_y_data.pgz'):
    print "-->Pickle found, loading x and y directly"
    with gzip.GzipFile('cache/x_y_data.pgz', 'r') as f:
      x, y = pickle.load(f)
  else:
    os.mkdir('cache')
    # Load the metadata
    print "-->Loading Metadata"
    metadata = load_metadata('data/metadata_all.tsv')
    
    # Set up the inputs and output containers 
    samples = len(metadata)
    x=np.ndarray(shape=(samples, metadata[0]['x'], metadata[0]['y']))
    y=np.ndarray(shape=(samples, 3)) 
    solid_vel=np.ndarray(shape=(samples, 3)) 

    # For each sample sim in our dataset:
    print "-->Constructing X"
    i = 0
    for metadatum in metadata:
      # Load data frames
      print "--->Loading: " + metadatum['filename']
      al_chunk = load_data('data/test/'+metadatum['filename'])
      # Get a representative slice from the block (or ave or whatever we decide on)
      best_slice = get_best_slice(al_chunk)
      x[i] = best_slice 
      y[i,0] = metadatum['ag']
      y[i,1] = metadatum['cu']
      y[i,2] = metadatum['sv']
      solid_vel[i] = metadatum['sv']
      i += 1
    print "-->Pickling x and y"
    with gzip.GzipFile('cache/x_y_data.pgz', 'w') as f:
      pickle.dump((x,y), f)

  # PCA component variance plot
  #plot_component_variance(x, y[:,2])
  
  # Plot components in pca space
#  plot_components(x,y, 5, linear_model.LinearRegression())

  if os.path.isfile('cache/x_corr.pgz'):
    with gzip.GzipFile('cache/x_corr.pgz', 'r') as f:
      print '-->Correlations found unpickling'
      x_corr, x_corr_flat = pickle.load(f)
  else:
    # Get correlations
    x_corr, x_corr_flat = compute_correlations(x)
    with gzip.GzipFile('cache/x_corr.pgz', 'w') as f:
      pickle.dump((x_corr, x_corr_flat), f)
  
  # Use PCA on flattened correlations
  x_pca = compute_pca_scores(x_corr_flat)
# LINEAR 
  print "-->Homogenizing"
  with open('data/linker_results_r2_data.csv', 'w') as csv_file:
    csv_writer = csv.writer(csv_file, delimiter=',')

    with open('data/linker_results_mse_data.csv', 'w') as csv_file_mse:
      csv_writer_mse = csv.writer(csv_file_mse, delimiter=',')
      print "--->LinearRegression"
      linker = linear_model.LinearRegression() 
      r2_mean, r2_std, mse_mean, mse_std = run_conventional_linkage(y,x_pca,5,linker)
      csv_writer.writerow(['LinearRegression', r2_mean, r2_std])
      csv_writer_mse.writerow(['LinearRegression', mse_mean, mse_std])
     
      print "--->Lasso"
      linker = linear_model.Lasso() 
      r2_mean, r2_std, mse_mean, mse_std = run_conventional_linkage(y,x_pca,5,linker)
      csv_writer.writerow(['Lasso', r2_mean, r2_std])
      csv_writer_mse.writerow(['Lasso', mse_mean, mse_std])
      
      print "--->Ridge"
      linker = linear_model.Ridge() 
      r2_mean, r2_std, mse_mean, mse_std = run_conventional_linkage(y,x_pca,5,linker)
      csv_writer.writerow(['Ridge', r2_mean, r2_std])
      csv_writer_mse.writerow(['Ridge', mse_mean, mse_std])

      # NON linear
#      print "--->LinearSVR"
#      linker = svm.LinearSVR()
#      r2_mean, r2_std, mse_mean, mse_std = run_conventional_linkage(y,x_pca,5,linker)
#      csv_writer.writerow(['LinearSVR', r2_mean, r2_std])
#      csv_writer_mse.writerow(['LinearSVR', mse_mean, mse_std])
      
#      print "--->nuSVR"
#      linker = svm.NuSVR() 
#      r2_mean, r2_std, mse_mean, mse_std = run_conventional_linkage(y,x_pca,5,linker)
#      csv_writer.writerow(['nuSVR', r2_mean, r2_std])
#      csv_writer_mse.writerow(['nuSVR', mse_mean, mse_std])
      
      print "--->TreeRegressor"
      linker = tree.DecisionTreeRegressor() 
      r2_mean, r2_std, mse_mean, mse_std = run_conventional_linkage(y,x_pca,5,linker)
      csv_writer.writerow(['TreeRegressor', r2_mean, r2_std])
      csv_writer_mse.writerow(['TreeRegressor', mse_mean, mse_std])
      
      print "--->RandomTreeRegressor"
      linker = tree.ExtraTreeRegressor() 
      r2_mean, r2_std, mse_mean, mse_std = run_conventional_linkage(y,x_pca,5,linker)
      csv_writer.writerow(['RandomForest', r2_mean, r2_std])
      csv_writer_mse.writerow(['RandomForest', mse_mean, mse_std])

  quit()



  print "-->Constructing Correlations"
  prim_basis = PrimitiveBasis(n_states=3, domain=[0,2])
  x_ = prim_basis.discretize(x)
  x_corr = correlate(x_, periodic_axes=[0, 1])
  x_corr_flat = np.ndarray(shape=(samples,  x_corr.shape[1]*x_corr.shape[2]*x_corr.shape[3]))
  row_ctr = 0
  for row in x_corr:
    x_corr_flat[row_ctr] = row.flatten() 
 
  print x.shape
  flat_len = (x.shape[0],) + (np.prod(x.shape[1:]),)
  X_train, X_test, y_train, y_test = train_test_split(x.reshape(flat_len), y,
                                                    test_size=0.2, random_state=3)
  print(x_corr.shape)
  print(X_test.shape) 
  # uncomment to view one containers
  #draw_correlations(x_corr[0].real)
  
  # Reduce all 2-pt Stats via PCA
  # Try linear reg on inputs and outputs
  reducer = PCA(n_components=3)
  linker = LinearRegression() 
  model = MKSHomogenizationModel(basis=prim_basis,
                                 compute_correlations=False)
  
  #model.fit(x_corr, y, periodic_axes=[0, 1]) 
  # set up parameters to optimize 
  params_to_tune = {'degree': np.arange(1, 4), 'n_components': np.arange(1, 8)}
  fit_params = {'size':x_corr_flat.shape, 'periodic_axes': [0, 1]}
  loo_cv = LeaveOneOut(samples)
  gs = GridSearchCV(model, params_to_tune, cv=loo_cv, n_jobs=6, fit_params=fit_params).fit(x_corr_flat, y)

  # Manual fit
  #model.fit(x_corr, y, periodic_axes=[0, 1]) 
  #print model.reduced_fit_data

  # Draw the plot containing the PCA variance accumulation
  #draw_component_variance(model.dimension_reducer.explained_variance_ratio_)

  draw_components([model.reduced_fit_data[0:3, :2], 
                   model.reduced_fit_data[3:6, :2],
                   model.reduced_fit_data[6:9, :2],
                   model.reduced_fit_data[9:11, :2]], ['0.0525', '0.0593', '0.0773','0.0844']) 
  print('Order of Polynomial'), (gs.best_estimator_.degree)
  print('Number of Components'), (gs.best_estimator_.n_components)
  print('R-squared Value'), (gs.score(X_test, y_test)) 
 
  #draw_components([model.reduced_fit_data[0:3, :2], 
  #                 model.reduced_fit_data[3:6, :2],
  #                 model.reduced_fit_data[6:9, :2],
  #                 model.reduced_fit_data[9:11, :2],
  #                 model.reduced_fit_data[11:, :2]], ['0.0525', '0.0593', '0.0773','0.0844', '>0.6']) 
  


