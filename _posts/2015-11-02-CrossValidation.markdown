---
layout:     post
title:     Modeling Process-Structure Behavior (Post) 
date:       2015-11-01 
author:    Robert Pienta 
tags: 		In Progress
---
<!-- Start Writing Below in Markdown -->


# Cross-validation & Optimization
This post heavily utilizes cross-validation and parameter optimization. 
We have implemented a pipeline that performs both of these using Scikit-Learn, pyMKS and NumPy.

Our cross-validation module allows for different types of cross-validators.

# Linear Models
We have finished our analysis of the different linear models and present the results below.

## Linear Regression
Model form:
$$y_i = \beta_1 x_1 + \beta_2 x_2 + ... + \beta_n x_n + \epsilon$$

More concisely:
$$ y = X\beta + \epsilon$$

This is a the ordinary least squares approach discussed in class.

## Polynomial Fits 
We used polynomial interpolation to model different potential representations for our data.
We performed this by creating a new set of features consisting of the polynomial combinations of our features.
We then performed OLS linear regression on the new feature space to find the best fit in the new space.
We tested only modest degrees as high degree polynomials are likely to heavily over-fit the our data. 

## Ridge Regression

## Lasso Regression

# Non-linear Models
We have started an initial investigation into different techniques to perform our regression task.

## Trees
We are now experimenting with trees to perform our regression. 
Decision trees are constructed by splitting the starting data using a single threshold over one input feature. 
The two remaining sets of inputs may then be recursively split in the same fashion until only a single datapoint is left in each subset--a leaf.
The leaves are then used to predict a particular set of output values based on the features of the data in the leaf. 
Once the decision tree has been created, the test data can be regressed by taking each test point and running it through the tree.
Each input must end up in a leaf, and that leaf's values are used as the prediction for the regression for that test datum.

An example from our data might look like this:  
![tree_view](/MIC-Ternary-Eutectic-Alloy/img/models_post/tree_example.png)


#Performance
![linear_view](/MIC-Ternary-Eutectic-Alloy/img/models_post/linear_example.png)
While several of the high-degree polnoymials were able to fit the data well, CV shows that those results were over-fit.


