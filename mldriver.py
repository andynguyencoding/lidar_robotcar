import pickle
import pandas as pd
from io import StringIO

selected_feature_indices = [24, 29, 31, 35, 38, 39, 40, 41, 42, 43, 44, 45, 47, 50, 54, 55, 57, 302,
                            304, 312, 314, 315, 316, 318, 319, 321, 324, 326, 328, 330]

filename = 'self_driving_model_0.1.pkl'
# Load the model from disk
with open(filename, 'rb') as file:
    model = pickle.load(file)


def predict_dir(in_str):
    # Read the string into a DataFrame
    ar = pd.read_csv(StringIO(in_str), sep=',', header=None)
    df = ar.iloc[:, selected_feature_indices]

    # Make predictions on the testing data
    return model.predict(df)


if __name__ == '__main__':
    str_input = ('0,2346.75,0,2249.0,2165.75,0,2084.25,2008.5,1943.0,0,1885.0,1827.0,0,1775.5,1728.25,1686.5,0,0.0,0,'
                 '1286.75,0.0,1252.5,0,0.0,0,812.25,797.5,0,783.0,770.25,786.25,0,0.0,0,1320.0,0,0,0,0.0,0.0,0,0.0,'
                 '0.0,0,0.0,0.0,0.0,0,1182.25,0.0,0,0.0,0,0.0,0,0,0.0,0,0.0,0.0,641.75,0,640.25,640.5,0,644.75,'
                 '661.75,663.75,0,666.0,670.5,678.75,0,0,0.0,0,0,1699.0,0,1705.75,0.0,0,0,1528.25,0.0,0,0.0,1235.75,'
                 '0,0.0,1182.0,0,1128.0,1128.75,0,0,0.0,0,829.0,844.75,861.5,0.0,0.0,910.5,0,866.5,852.5,0,836.0,'
                 '778.25,783.5,0,814.25,745.25,0,746.75,756.75,773.5,0,0,0,0,0,332.25,329.5,0.0,325.0,0,0,0,0,248.0,'
                 '0,0,253.75,0,257.75,0.0,0,0,0.0,0.0,0.0,0,0.0,0,290.25,0.0,677.25,0,699.0,718.5,724.5,0.0,717.5,'
                 '701.0,0,682.0,662.25,0,643.5,625.0,0,611.5,606.25,613.25,641.5,0,717.5,746.25,751.25,0,746.75,'
                 '738.0,0,723.75,710.75,701.75,0,696.25,698.75,0,0,840.0,861.0,0,861.25,853.0,842.25,0,0,0,370.5,0,0,'
                 '0,0,0.0,0,0.0,0.0,0,0.0,0.0,0.0,0.0,501.75,0.0,0,0.0,0,0,0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0.0,2646.5,'
                 '0.0,2628.75,0.0,2673.0,0.0,1702.75,1724.5,0,1720.5,1717.75,0,1718.0,1716.75,1719.75,0,1723.25,'
                 '1724.0,0,1729.25,1735.75,1740.5,0,1750.25,1761.0,0,1768.25,1780.5,1795.75,0,1808.5,1824.5,0,'
                 '1837.75,1859.25,1883.25,0,1899.25,1924.0,0,0,0,491.25,451.25,0,423.75,0,406.5,389.5,0,369.0,361.75,'
                 '0,354.5,346.5,0,338.75,331.5,0,322.0,321.0,0,300.25,0,293.0,289.5,290.5,291.25,0,291.5,0,288.25,'
                 '278.25,0,280.25,286.25,0,292.5,295.5,295.0,296.75,0,313.75,0,0,0,0.0,0.0,8025.5,7937.5,0.0,7882.75,'
                 '7827.5,7769.5,0,0,0,0,0,0,0,3760.75,0,5058.75,0.0,4743.25,0.0,0.0,3693.25,4294.5,4397.25,0,4512.75,'
                 '4677.0,0.0,0,5068.5,5088.0,0,0.0,0.0,0,0.0,2774.25,2581.5,0,2603.5,2620.0,0,2366.0,0,0.00,2188.25,'
                 '0,2211.5,2230.75,0.0,2457.5')
    print(predict_dir(str_input))
