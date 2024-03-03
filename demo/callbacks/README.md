# Callback Guide for Flask-Schema

## Introduction

Callbacks are a powerful feature of `flask-scheema` that allow you to customize the behavior of your API. This guide
provides an overview of the available callbacks and how to use them to enhance your API.

## Getting Started

To use callbacks in your API, you need to define a callback function first. A callback function is a function that is
called at a specific point in the API's lifecycle. You can define a callback function to perform custom logic, such as
logging, error handling etc.

## Lifecycle Callbacks

> SETUP_CALLBACKS - This callback is called prior to the database query being executed. It is useful for setting up
                  preconditions for the query, such as logging, error handling. 


> RETURN_CALLBACKS - This callback is called after the database query has been executed. It is useful for performing
                     post-processing on the query results, such as logging, error handling.

> ERROR_CALLBACKS - This callback is called when an error occurs during the database query. It is useful for handling
                    errors and logging.

## Callback Functions

View the `callbacks.py` file in the root of this directory to see the callback functions created for this API. 

They have been applied at a global, and model specific level, for more information on this you can view.
