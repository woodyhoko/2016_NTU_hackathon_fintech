# coding: utf-8
 
# 加入圖表功能
 
# In[52]:
 
import matplotlib.pyplot as plt
 
 
# PID控制函數
 
# In[53]:
 
def pidcontrol(x,target,h=1,Ki=1,Kd=1,Kp=0.005,ie=0,de=0):
    e=target-x
    i=Ki*1*h*e+ie
    d=Kd*1*(e-de)/h
 
    return Kp*(e+i+d),e,h*e
 
 
# 初始輸入數值
 
# In[84]:
 
print("initial price:",end='')
x=int(input())
print("initial needs:",end='')
need0=int(input())
print("the product kind:",end='')
productclass=input()
print("the first situation")
print("the left over production rate:",end='')
b1=int(input())
print("the increased needs rate:",end='')
g1=int(input())
print("the second situation")
print("the left over production rate:",end='')
b2=int(input())
print("the increased needs rate:",end='')
g2=int(input())
print("the third situation")
print("the left over production rate:",end='')
b3=int(input())
print("the increased needs rate:",end='')
g3=int(input())
demandslope=0
productcase=0
target=['']*4
need=['']*4
target[0]=x
 
if productclass=="a":
    productcase=0.001
    target[1]=x-target[0]*(b1/150)+target[0]*g1/150
    target[2]=target[1]-target[0]*(b2/150)+target[0]*g2/150
    target[3]=target[2]-target[0]*(b3/150)+target[0]*g3/150
    need[1]=x+x*(b1/150)-x*g1/150
    need[2]=need[1]+need[1]*(b2/150)-need[1]*g2/150
    need[3]=need[2]+need[2]*(b3/150)-need[2]*g3/150
    demandslope=-1.5
elif productclass=="b":
    productcase=0.005
    target[1]=x-target[0]*(b1/200)+target[0]*g1/200
    target[2]=target[1]-target[0]*(b2/200)+target[0]*g2/200
    target[3]=target[2]-target[0]*(b3/200)+target[0]*g3/200
    need[1]=x+need0*(b1/200)+need0*g1/200
    need[2]=need[1]+need0*(b2/200)+need0*g2/200
    need[3]=need[2]+need0*(b3/200)+need0*g3/200
    demandslope=-1
else:
    productcase=0.01
    target[1]=x-x*(b1/400)+x*g1/400
    target[2]=target[1]-target[1]*(b2/400)+target[1]*g2/400
    target[3]=target[2]-target[2]*(b3/400)+target[2]*g3/400
    need[1]=x+x*(b1/400)-x*g1/400
    need[2]=need[1]+need[1]*(b2/400)-need[1]*g2/400
    need[3]=need[2]+need[2]*(b3/400)-need[2]*g3/400
    demandslope=-0.5
time=1
de=0
ie=0
oldway=0
statisdem=0
statissup=0
 
need[0]=need0
 
 
 
 
# 初步純數值運算
 
# In[85]:
 
xx=x
time=1
de=0
ie=0
oldway=0
statisdem=0
statissup=0
number=['']*192
price=['']*192
demandnew=['']*192
demandold=['']*192
supplynew=['']*192
supplyold=['']*192
for n in range(4):
    for h in range(1,49):
        needtemp=0
        print(time,xx)
        number[time-1]=time
        price[time-1]=xx
        xx+=pidcontrol(xx,target[n],h,Kp=productcase,de=de,ie=ie)[0]
        de=pidcontrol(xx,target[n],h,Kp=productcase,de=de,ie=ie)[1]
        ie=pidcontrol(xx,target[n],h,Kp=productcase,de=de,ie=ie)[2]
        if ((xx-target[n])/demandslope)+need[n]<(xx-target[n])+need[n]:
            needtemp=((xx-target[n])/demandslope)+need[n]
        else:
            needtemp=(xx-target[n])+need[n]
        demandm=0
        olddem=0
        supplym=0
        oldsup=0
        for m in range(int(needtemp)):
            demandm+=(demandslope*(m-need[n])+target[n])-xx
            if (m-need[n])+target[n]>0:
                supplym+=xx-((m-need[n])+target[n])
            else:
                supplym+=xx 
        if n!=0:
            for m in range(int(need[n-1])):
                olddem+=(demandslope*(m-need[n])+target[n])-target[n-1]
                if (m-need[n])+target[n]>0:
                    oldsup+=target[n-1]-((m-need[n])+target[n])
                else:
                    oldsup+=target[n-1]
        else:
            for m in range(int(need[0])):
                olddem+=(demandslope*(m-need[0])+target[0])-target[0]
                if (m-need[0])+target[0]>0:
                    oldsup+=target[0]-((m-need[0])+target[0])
                else:
                    oldsup+=target[0]
 
        demandnew[time-1]=demandm
        demandold[time-1]=olddem
        supplynew[time-1]=supplym
        supplyold[time-1]=oldsup
        statisdem+=demandm-olddem
        statissup+=supplym-oldsup
        time+=1
 
 
 
 
# 價格變動圖表
 
# In[86]:
 
get_ipython().magic('matplotlib inline')
plt.plot(number,price)
plt.axvline(48,color='g', linestyle='--')
plt.axvline(96,color='g', linestyle='--')
plt.axvline(144,color='g', linestyle='--')
plt.axvline(192,color='g', linestyle='--')
plt.axis([0,200,0,max(price)+10])
plt.show()
print(target[0],'->',target[1],'->',target[2],'->',target[3])
 
 
# 消費者剩餘，舊版新版比較差異圖表
 
# In[87]:
 
sumdemand=list(map(lambda x,y:x-y,demandnew,demandold))
plt.axvline(48,color='g', linestyle='--')
plt.axvline(96,color='g', linestyle='--')
plt.axvline(144,color='g', linestyle='--')
plt.axvline(192,color='g', linestyle='--')
plt.plot(number,demandnew,number,demandold,'r',number,sumdemand,'k')
plt.show()
 
 
# 消費者剩餘差異的累計圖表
 
# In[88]:
 
sumdemanda=['']*192
for n in range(len(sumdemand)-1,-1,-1):
    sumdemanda[n]=sum(sumdemand[0:n])
plt.axvline(48,color='g', linestyle='--')
plt.axvline(96,color='g', linestyle='--')
plt.axvline(144,color='g', linestyle='--')
plt.axvline(192,color='g', linestyle='--')
plt.plot(number,sumdemanda,'k')
plt.show()
print(sumdemand[-1])
 
 
# 生產者剩餘，舊版新版比較差異圖表
 
# In[89]:
 
sumsupply=list(map(lambda x,y:x-y,supplynew,supplyold))
plt.axvline(48,color='g', linestyle='--')
plt.axvline(96,color='g', linestyle='--')
plt.axvline(144,color='g', linestyle='--')
plt.axvline(192,color='g', linestyle='--')
plt.plot(number,supplynew,number,supplyold,'r',number,sumsupply,'k')
plt.show()
 
 
# 生產者剩餘差異的累計圖表
 
# In[90]:
 
sumsupplya=['']*192
for n in range(len(sumsupply)-1,-1,-1):
    sumsupplya[n]=sum(sumsupply[0:n])
plt.axvline(48,color='g', linestyle='--')
plt.axvline(96,color='g', linestyle='--')
plt.axvline(144,color='g', linestyle='--')
plt.axvline(192,color='g', linestyle='--')
plt.plot(number,sumsupplya,'k')
plt.show()
print(sumsupply[-1])
 
 
# 總剩餘，舊版新版比較差異圖表
 
# In[91]:
 
sumnew=list(map(lambda x,y:x+y,supplynew,demandnew))
sumold=list(map(lambda x,y:x+y,supplyold,demandold))
suminall=list(map(lambda x,y:x-y,sumnew,sumold))
plt.axvline(48,color='g', linestyle='--')
plt.axvline(96,color='g', linestyle='--')
plt.axvline(144,color='g', linestyle='--')
plt.axvline(192,color='g', linestyle='--')
plt.plot(number,sumnew,number,sumold,'r',number,suminall,'k')
plt.show()
 
 
# 總剩餘差異的累計圖表
 
# In[92]:
 
suminalla=['']*192
for n in range(len(suminall)-1,-1,-1):
    suminalla[n]=sum(suminall[0:n])
plt.axvline(48,color='g', linestyle='--')
plt.axvline(96,color='g', linestyle='--')
plt.axvline(144,color='g', linestyle='--')
plt.axvline(192,color='g', linestyle='--')
plt.plot(number,suminalla,'k')
plt.show()
print(suminalla[-1])
 
 
# In[74]:
 
open('data.txt', 'w').close()
f=open('data.txt','a')
f.write("class : ")
f.write(productclass)
f.write(' . ')
f.write('initial price : ')
f.write(str(x))
f.write(' . ')
f.write('initial needs : ')
f.write(str(need0))
f.write('\n')
for i in range(3):
    f.write(str(number[i]))
    f.write(' . ')
    f.write(str(target[i]))
    f.write(' . ')
    f.write(str(need[i]))
    f.write('\n')
f.write
for n in range(192):
    f.write(str(number[n]))
    f.write(' . ')
    f.write(str(price[n]))
    f.write(' . ')
    f.write(str(demandnew[n]))
    f.write(' . ')
    f.write(str(demandold[n]))
    f.write(' . ')
    f.write(str(supplynew[n]))
    f.write(' . ')
    f.write(str(supplyold[n]))
    f.write("\n")
f.close()
