# lidar_robotcar

## Introduction
Using Lidar with Machine Learning to build a self-driving car solution.

## Electronics components
The documentation is in docs folder. All the electronics parts are listed here.

## Steps to train ML model
After assemble the car, you first need to do data collection. This is done by put the car into data collection mode. After that, we then drive the car manually. Once we are happy with data collection press button "A" on your joystick (depends on your joystick model, it can be different key) to stop.

The next step is to visualize the data and clean it. This can be done using the program visualizer.py.

Then go ahead with training the model using Random Forest Regressor from Scikit-Learn. This is done using the Jupyter notebook in the notebooks folder.

## References
Murtaza, Youtube How to run robot motors: https://youtu.be/0lXY87NwVIc?si=XjZ9y-pofpmrJ3lj <br />
Murtaza, Youtube How to run joystick with Raspberry Pi: https://youtu.be/TMBfiS7LNnU?si=BKFeUhWR-5dlGu2r <br />
Github, The origin Python library used with RP Lidar - Robotica/RPLidar: https://github.com/Roboticia/RPLidar <br />
Nikodem Bartik visualizer Python program: https://www.youtube.com/watch?v=PdSDhdciSpE&t=1s
