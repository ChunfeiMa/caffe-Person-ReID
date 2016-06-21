
# coding: utf-8

# In[1]:

import numpy as np
#import matplotlib.pyplot as plt
import math
#get_ipython().magic(u'matplotlib inline')

# Make sure that caffe is on the python path:
caffe_root = '../' 
import sys
sys.path.insert(0, caffe_root + 'python')

import caffe
import fileinput
#plt.rcParams['figure.figsize'] = (10, 10)
#plt.rcParams['image.interpolation'] = 'nearest'
#plt.rcParams['image.cmap'] = 'gray'

import os


# In[2]:

#getDiff Implementation
def getDiff( vector1, vector2 ):
    sum=0
    for i in range(50):
        for j in range(1024):
            diff= vector1[i][j]-vector2[i][j]
            diff=diff*diff
            sum=sum+diff
        
    return math.sqrt(sum)


# In[3]:

caffe.set_device(0)
caffe.set_mode_gpu()
net = caffe.Net(caffe_root +  'examples/_temp/unsup_net_deploy.prototxt',
                    caffe_root + 'rank_scripts/models10/_iter_600.caffemodel',
                    caffe.TEST)# input preprocessing: 'data' is the name of the input blob == net.inputs[0]

transformer = caffe.io.Transformer({'data': net.blobs['data'].data.shape})
transformer.set_transpose('data', (2,0,1))
transformer.set_mean('data', np.load(caffe_root + 'rank_scripts/market_query_mean_128x64.npy').mean(1).mean(1)) # mean pixel
transformer.set_raw_scale('data', 255)  # the reference model operates on images in [0,255] range instead of [0,1]
transformer.set_channel_swap('data', (2,1,0))  # the reference model has channels in BGR order instead of RGB


# In[4]:

#Rank Vector Setup
num_rank = 6

#source of query folder
query_folder = sys.argv[1]
images_list = os.listdir(query_folder)


# In[12]:

images_features = {}

for image in images_list:
    net = caffe.Net(caffe_root +  'examples/_temp/unsup_net_deploy.prototxt',
                    caffe_root + 'rank_scripts/models10/_iter_600.caffemodel',
                    caffe.TEST)# input preprocessing: 'data' is the name of the input blob == net.inputs[0]

    # set net to batch size of 100
    net.blobs['data'].reshape(100,3,64,64)

    query_image_path = 'rank_scripts/images_market/' + image
    query_image = caffe.io.load_image(caffe_root + query_image_path)
    net.blobs['data'].data[...] = transformer.preprocess('data', query_image)
    out = net.forward()
    images_features[image]=out['fc7']


# In[18]:

#print images_features['0026_c2s1_001626_00.jpg']


# In[19]:

file1 = open('market_cmc.txt','w')

images_set= []

for line in fileinput.input('query_set.txt'):
	images_set.append(line[:-1])

for image_q in images_set:
    
    vector_query = images_features[image_q]
    #plt.figure(figsize=(3,3))
    #plt.imshow(query_image)

    #Paired list to hold (diff,imagePath)

    Rank_list= []

    #print images_list

    for image in images_list:

        vector_new=images_features[image]
        diff = getDiff(vector_query, vector_new)

        #add the pair (diff,image) to the list
        Rank_list.append((diff,image))

        #sort the list based on diff
        Rank_list.sort()

        #remove the last element if more than 'num_rank'
        if len(Rank_list) > num_rank :
            Rank_list.remove(Rank_list[len(Rank_list)-1])

    file1.write(image_q)
    file1.write(',')
    
    for item in Rank_list:
        file1.write(item[1])
        
        if item is Rank_list[len(Rank_list)-1]:
            file1.write('\n')
        else:
            file1.write(',')
    
file1.close()

