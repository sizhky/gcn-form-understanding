import torch.utils.data as data
import glob

from utils import *
from random import randrange
from dgl.nn.pytorch import GATConv, GraphConv
import matplotlib.pyplot as plt
import dgl.function as fn

from torch import nn
import torch

import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import os
import sys
import sklearn

import numpy as np
import xml.etree.ElementTree as ET
import networkx as nx
import pdb
"""## Import libraries"""
import pagexml
import re
import torch 
import dgl
from torch.optim.lr_scheduler import StepLR
from torch.utils.data import DataLoader

from model import Net
from datasets import FUNSD,collate

def test_grouping(bg,prediction,target):

    rec = float(((prediction == target)[target.bool()].float().sum()/target.sum()).item())
    prec = float(((prediction == target)[prediction.bool()].float().sum()/prediction.sum()).item())


    # GT AND PRED COMPONENTS

    pred_edges = torch.t(torch.stack([bg.edges()[0][prediction.bool()],bg.edges()[1][prediction.bool()]]))
    predg = edges_list_to_dgl_graph(pred_edges)
    predg.ndata['position']=bg.ndata['position']
    
    pred_components = nx.connected_components(predg.to_networkx().to_undirected())
    
    target_edges = torch.t(torch.stack([bg.edges()[0][target.bool()],bg.edges()[1][target.bool()]]))
    yg = edges_list_to_dgl_graph(target_edges)
    yg.ndata['position']=bg.ndata['position']
    
    gt_components = nx.connected_components(yg.to_networkx().to_undirected())
    cluster_idx=0
    pred_node_labels=np.zeros(bg.number_of_nodes())
    all_nodes = []
    for node_cluster in pred_components:
        for node in node_cluster:
            all_nodes.append(node)
            pred_node_labels[node]=cluster_idx
        cluster_idx+=1
    cluster_idx=0
    gt_node_labels=np.zeros(bg.number_of_nodes())

    for node_cluster in gt_components:
        for node in node_cluster:
            gt_node_labels[node]=cluster_idx
        cluster_idx+=1
    
    ari = sklearn.metrics.adjusted_rand_score(gt_node_labels,pred_node_labels)


    return prec,rec,ari



def test_labeling(input_graph,entity_class,entity_position,entity_labels):
    entity_labels = entity_labels[0]
    pred_classes = torch.argmax(entity_class,dim=1)
    distance_threshold = 5.
    number_of_classes  =int(entity_labels[:,0].max())+1
    precisions={}
    recalls={}
    for category in range(number_of_classes):
        true_positives=0.
        pred_entity_indices = torch.where(pred_classes == category)[0]
        gt_entity_indices = torch.where(entity_labels[:,0]==category)[0]
        if pred_entity_indices.numel()<1 or gt_entity_indices.numel()<1: continue
        for gt_idx in gt_entity_indices:
            for pred_idx in pred_entity_indices:
                if torch.norm(entity_position[pred_idx,:]-entity_labels[gt_idx,1:])<distance_threshold:
                    true_positives+=1

                    break
        precisions[category]=true_positives/max(int((pred_classes==category).sum()),1e-10)
        recalls[category]=true_positives/max(int((entity_labels[:,0]==category).sum()),1e-10)


    precision,recall= np.mean([p for p in precisions.values()]),np.mean([r for r in recalls.values()])
    
    return precision,recall