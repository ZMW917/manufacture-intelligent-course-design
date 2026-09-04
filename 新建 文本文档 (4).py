from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor

#模拟14天合格率数据
history = np.array([[i] for i in range(14)])
rate = np.array([0.8+np.random.randn()*0.05 for _ in range(14)])

gbr = GradientBoostingRegressor()
lr = LinearRegression()
gbr.fit(history,rate)
lr.fit(history,rate)

#预测未来7天
future_x = np.array([[14+i] for i in range(7)])
pred_gbr = gbr.predict(future_x)
pred_lr = lr.predict(future_x)

#±2σ异常判断
mu = np.mean(rate)
sigma = np.std(rate)
upper = mu + 2*sigma
lower = mu - 2*sigma
print("控制限 lower",lower,"upper",upper)