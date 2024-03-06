# lidar_robotcar

Using Lidar with Machine Learning to build a self-driving car solution.
The documentation is in docs folder. All the electronics parts are listed here.

After assemble the car, you first need to do data collection. This is done by put the car into data collection mode. After that, we then drive the car manually. Once we are happy with data collection press button "A" on your joystick (depends on your joystick model, it can be different key) to stop.

The next step is to visualize the data and clean it. This can be done using the program visualizer.py.

Then go ahead with training the model using Random Forest Regressor from Scikit-Learn. This is done using the Jupyter notebook in the notebooks folder.
