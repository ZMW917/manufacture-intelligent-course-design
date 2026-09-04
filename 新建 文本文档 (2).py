from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import joblib

# --------模拟训练，实际这里应该传入很多样本的特征和标签
X = np.random.rand(21,10)   #模拟21条样本，对应PPT数据集
y = np.random.randint(0,7,size=21) #7类缺陷标签0‑6

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

#随机森林
rf = RandomForestClassifier(n_estimators=100, random_state=1)
rf.fit(X_scaled,y)

#SVM RBF核
svm = SVC(kernel="rbf", C=1.0, gamma="scale")
svm.fit(X_scaled,y)

#五折交叉验证
cv_score = cross_val_score(rf,X_scaled,y,cv=5)
print("随机森林五折验证：",cv_score.mean())

#模型持久化保存
joblib.dump(rf,"rf_model.pkl")
joblib.dump(scaler,"scaler.pkl")