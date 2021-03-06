# -*- coding: utf-8 -*-
"""N3_Multimedia_Termproject.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1z3IYeYpeVLbN9R7EpvDMx3GFEKNNg23t

# Get Dataset from Google Drive  
Please upload your dataset on google drive first.
"""

from google.colab import drive
drive.mount('/content/drive')

import os
import zipfile
import tqdm

file_name = "Multimedia_dataset.zip"
zip_path = os.path.join('/content/drive/MyDrive/Multimedia/Multimedia_dataset/Multimedia_dataset.zip')

!cp "{zip_path}" .
!unzip -q "{file_name}"
!rm "{file_name}"

"""# Noise Transform  
If you want to change how much noise you are giving, change the stddev and mean values at 'gaussian_noise' function.
"""

import torch
from torch.autograd import Variable
from torchvision import transforms

import random

class NoiseTransform(object):
  def __init__(self, size=180, mode="training"):
    super(NoiseTransform, self).__init__()
    self.size = size
    self.mode = mode
  
  def gaussian_noise(self, img):
    mean = 0
    stddev = 25
    noise = Variable(torch.zeros(img.size()))
    noise = noise.data.normal_(mean, stddev/255.)

    return noise

  def __call__(self, img):
    if (self.mode == "training") | (self.mode == "validation"):
      self.gt_transform = transforms.Compose([
        transforms.Resize((self.size, self.size), interpolation=2),
        transforms.ToTensor()])
      self.noise_transform = transforms.Compose([
        transforms.Resize((self.size, self.size), interpolation=2),
        transforms.ToTensor(),
        transforms.Lambda(self.gaussian_noise),
      ])
      return self.gt_transform(img), self.noise_transform(img)

    elif self.mode == "testing":
      self.gt_transform = transforms.Compose([
        transforms.ToTensor()])
      return self.gt_transform(img)
    else:
      return NotImplementedError

"""# Dataloader for Noise Dataset"""

import torch
import torch.utils.data  as data
import os
from PIL import Image
import numpy as np
import torch.nn as nn

import matplotlib.pyplot as plt

class NoiseDataset(data.Dataset):
  def __init__(self, root_path, size):
    super(NoiseDataset, self).__init__()

    self.root_path = root_path
    self.size = size
    self.transforms = None
    self.examples = None

  def set_mode(self, mode):
    self.mode = mode
    self.transforms = NoiseTransform(self.size, mode)
    if mode == "training":
      train_dir = os.path.join(self.root_path, "train")
      self.examples = [os.path.join(self.root_path, "train", dirs) for dirs in os.listdir(train_dir)]
    elif mode == "validation":
      val_dir = os.path.join(self.root_path, "validation")
      self.examples = [os.path.join(self.root_path, "validation", dirs) for dirs in os.listdir(val_dir)]
    elif mode == "testing":
      test_dir = os.path.join(self.root_path, "test")
      self.examples = [os.path.join(self.root_path, "test", dirs) for dirs in os.listdir(test_dir)]
    else:
      raise NotImplementedError
  
  def __len__(self):
    return len(self.examples)

  def __getitem__(self, idx):
    file_name = self.examples[idx]
    image = Image.open(file_name)


    if self.mode == "testing":
      input_img = self.transforms(image)
      sample = {"img": input_img}
    else:
      clean, noise = self.transforms(image)
      sample = {"img": clean, "noise": noise}

    return sample

"""# Example for Loading"""

import torch
import torch.utils.data  as data
import os
import matplotlib.pyplot as plt
from torchvision import transforms
import tqdm
from PIL import Image

def image_show(img):
  if isinstance(img, torch.Tensor):
    # PIL image??? ????????????.
    img = transforms.ToPILImage()(img)
  plt.imshow(img)
  plt.show()



# Change to your data root directory
root_path = "/content/"
# Depend on runtime setting
use_cuda = True

train_dataset = NoiseDataset(root_path, 128) #128??? size
train_dataset.set_mode("training")


# batch=4 ????????? data??? load
train_dataloader = data.DataLoader(train_dataset, batch_size=4, shuffle=True)
"""
# tqdm??? ???????????????
for i, data in enumerate(tqdm.tqdm(train_dataloader)):
  #CUDA??? NVIDIA?????? ????????? GPU ?????? ?????? ?????? ?????? ????????? ????????? ???????????? ?????? ??????
  if use_cuda:
    img = data["img"].to('cuda')
    noise = data["noise"].to('cuda')
  
  model_input = img + noise

  # clamp??? ?????? ?????? ?????? ???????????? ??????
  # (??????~?????? ????????? ???????????? ????????? ????????? ??? ?????? ?????? ??????????????? ??????)
  noise_image = torch.clamp(model_input, 0, 1)

  image_show(img[0])
  image_show(noise[0])



  input()
"""

"""# UNet Network"""

import os
import numpy as np

import torch
import torch.nn as nn


## ???????????? ????????????
class UNet(nn.Module):
    def __init__(self, nch, nker=64, learning_type="plain", norm="bnorm"):
        super(UNet, self).__init__()

        self.learning_type = learning_type

        # Contracting path
        self.enc1_1 = CBR2d(in_channels=nch, out_channels=1 * nker, norm=norm)
        self.enc1_2 = CBR2d(in_channels=1 * nker, out_channels=1 * nker, norm=norm)

        self.pool1 = nn.MaxPool2d(kernel_size=2)

        self.enc2_1 = CBR2d(in_channels=nker, out_channels=2 * nker, norm=norm)
        self.enc2_2 = CBR2d(in_channels=2 * nker, out_channels=2 * nker, norm=norm)

        self.pool2 = nn.MaxPool2d(kernel_size=2)

        self.enc3_1 = CBR2d(in_channels=2 * nker, out_channels=4 * nker, norm=norm)
        self.enc3_2 = CBR2d(in_channels=4 * nker, out_channels=4 * nker, norm=norm)

        self.pool3 = nn.MaxPool2d(kernel_size=2)

        self.enc4_1 = CBR2d(in_channels=4 * nker, out_channels=8 * nker, norm=norm)
        self.enc4_2 = CBR2d(in_channels=8 * nker, out_channels=8 * nker, norm=norm)

        self.pool4 = nn.MaxPool2d(kernel_size=2)

        self.enc5_1 = CBR2d(in_channels=8 * nker, out_channels=16 * nker, norm=norm)



        # Expansive path
        self.dec5_1 = CBR2d(in_channels=16 * nker, out_channels=8 * nker, norm=norm)

        self.unpool4 = nn.ConvTranspose2d(in_channels=8 * nker, out_channels=8 * nker,
                                          kernel_size=2, stride=2, padding=0, bias=True)

        self.dec4_2 = CBR2d(in_channels=2 * 8 * nker, out_channels=8 * nker, norm=norm)
        self.dec4_1 = CBR2d(in_channels=8 * nker, out_channels=4 * nker, norm=norm)

        self.unpool3 = nn.ConvTranspose2d(in_channels=4 * nker, out_channels=4 * nker,
                                          kernel_size=2, stride=2, padding=0, bias=True)

        self.dec3_2 = CBR2d(in_channels=2 * 4 * nker, out_channels=4 * nker, norm=norm)
        self.dec3_1 = CBR2d(in_channels=4 * nker, out_channels=2 * nker, norm=norm)

        self.unpool2 = nn.ConvTranspose2d(in_channels=2 * nker, out_channels=2 * nker,
                                          kernel_size=2, stride=2, padding=0, bias=True)

        self.dec2_2 = CBR2d(in_channels=2 * 2 * nker, out_channels=2 * nker, norm=norm)
        self.dec2_1 = CBR2d(in_channels=2 * nker, out_channels=1 * nker, norm=norm)

        self.unpool1 = nn.ConvTranspose2d(in_channels=1 * nker, out_channels=1 * nker,
                                          kernel_size=2, stride=2, padding=0, bias=True)

        self.dec1_2 = CBR2d(in_channels=2 * 1 * nker, out_channels=1 * nker, norm=norm)
        self.dec1_1 = CBR2d(in_channels=1 * nker, out_channels=1 * nker, norm=norm)

        self.fc = nn.Conv2d(in_channels=1 * nker, out_channels=nch, kernel_size=1, stride=1, padding=0, bias=True)


    # Unet Layer ?????? (Forwarding)
    # ????????? ????????? ?????? ???????????? ??????????????? ???????????? ???
    def forward(self, x):
        # forward encoder
        enc1_1 = self.enc1_1(x)
        enc1_2 = self.enc1_2(enc1_1)
        pool1 = self.pool1(enc1_2)

        enc2_1 = self.enc2_1(pool1)
        enc2_2 = self.enc2_2(enc2_1)
        pool2 = self.pool2(enc2_2)

        enc3_1 = self.enc3_1(pool2)
        enc3_2 = self.enc3_2(enc3_1)
        pool3 = self.pool3(enc3_2)

        enc4_1 = self.enc4_1(pool3)
        enc4_2 = self.enc4_2(enc4_1)
        pool4 = self.pool4(enc4_2)

        enc5_1 = self.enc5_1(pool4)

        # forward decoder
        dec5_1 = self.dec5_1(enc5_1)

        unpool4 = self.unpool4(dec5_1)
        # cat??? ?????? step??? output channel??? skip connection??? ??????????????? ??????
        # dim = [0: batch, 1: channel, 2: height, 3: width] <- dim??? ?????? ????????? ????????????.
        cat4 = torch.cat((unpool4, enc4_2), dim=1)
        dec4_2 = self.dec4_2(cat4)
        dec4_1 = self.dec4_1(dec4_2)

        unpool3 = self.unpool3(dec4_1)
        cat3 = torch.cat((unpool3, enc3_2), dim=1)
        dec3_2 = self.dec3_2(cat3)
        dec3_1 = self.dec3_1(dec3_2)

        unpool2 = self.unpool2(dec3_1)
        cat2 = torch.cat((unpool2, enc2_2), dim=1)
        dec2_2 = self.dec2_2(cat2)
        dec2_1 = self.dec2_1(dec2_2)

        unpool1 = self.unpool1(dec2_1)
        cat1 = torch.cat((unpool1, enc1_2), dim=1)
        dec1_2 = self.dec1_2(cat1)
        dec1_1 = self.dec1_1(dec1_2)

        if self.learning_type == "plain":
            x = self.fc(dec1_1)
        elif self.learning_type == "residual":
            x = x + self.fc(dec1_1)

        return x
  
## ???????????? ????????????
def save(ckpt_dir, net, optim, epoch):
    if not os.path.exists(ckpt_dir):
        os.makedirs(ckpt_dir)

    torch.save({'net': net.state_dict(), 'optim': optim.state_dict()},
               "%s/model_epoch%d.pth" % (ckpt_dir, epoch))

## ???????????? ????????????
def load(ckpt_dir, net, optim):
    if not os.path.exists(ckpt_dir):
        epoch = 0
        return net, optim, epoch

    ckpt_lst = os.listdir(ckpt_dir)
    ckpt_lst.sort(key=lambda f: int(''.join(filter(str.isdigit, f))))

    dict_model = torch.load('%s/%s' % (ckpt_dir, ckpt_lst[-1]))

    net.load_state_dict(dict_model['net'])
    optim.load_state_dict(dict_model['optim'])
    epoch = int(ckpt_lst[-1].split('epoch')[1].split('.pth')[0])

    return net, optim, epoch


class CBR2d(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size=3, stride=1, padding=1, bias=True, norm="bnorm", relu=0.0):
        super().__init__()

        layers = []
        layers += [nn.Conv2d(in_channels=in_channels, out_channels=out_channels,
                             kernel_size=kernel_size, stride=stride, padding=padding,
                             bias=bias)]

        if not norm is None:
            if norm == "bnorm":
                layers += [nn.BatchNorm2d(num_features=out_channels)]
            elif norm == "inorm":
                layers += [nn.InstanceNorm2d(num_features=out_channels)]

        if not relu is None and relu >= 0.0:
            layers += [nn.ReLU() if relu == 0 else nn.LeakyReLU(relu)]

        self.cbr = nn.Sequential(*layers)

    def forward(self, x):
        return self.cbr(x)

"""# Trainer"""

import argparse

import os
import numpy as np

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter


import matplotlib.pyplot as plt

from torchvision import transforms


## ???????????? ???????????? ????????????
train_continue = "off"

lr = 1e-3
batch_size = 100
num_epoch = 100

ckpt_dir = "/content/drive/MyDrive/Multimedia/Termproject/checkpoint/"
log_dir = "/content/drive/MyDrive/Multimedia/Termproject/log"
result_dir = "/content/drive/MyDrive/Multimedia/Termproject/result"

task = 'denoising'
opts = ['random', 4]


nch = 3
nker = 64

learning_type = 'plain'

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')



print("learning rate: %.4e" % lr)
print("batch size: %d" % batch_size)
print("number of epoch: %d" % num_epoch)

print("task: %s" % task)
print("opts: %s" % opts)

print("learning type: %s" % learning_type)

print("ckpt dir: %s" % ckpt_dir)
print("log dir: %s" % log_dir)
print("result dir: %s" % result_dir)

print("device: %s" % device)

## ???????????? ????????????
result_dir_train = os.path.join(result_dir, 'train')
result_dir_val = os.path.join(result_dir, 'val')

if not os.path.exists(result_dir):
    os.makedirs(os.path.join(result_dir_train, 'png'))
    # os.makedirs(os.path.join(result_dir_train, 'numpy'))

    os.makedirs(os.path.join(result_dir_val, 'png'))
    # os.makedirs(os.path.join(result_dir_val, 'numpy'))

    os.makedirs(os.path.join(result_dir_test, 'png'))
    os.makedirs(os.path.join(result_dir_test, 'numpy'))


# Change to your data root directory
root_path = "/content/"
# Depend on runtime setting
use_cuda = True



# training dataset ????????????
dataset_train = NoiseDataset(root_path, 128) #128??? size
dataset_train.set_mode("training")
loader_train = DataLoader(dataset_train, batch_size=batch_size, shuffle=True)



# validation dataset????????????
dataset_val = NoiseDataset(root_path, 128) #128??? size
dataset_val.set_mode("validation")
loader_val = DataLoader(dataset_val, batch_size=batch_size, shuffle=True)



# ????????? ???????????? variables ????????????
num_data_train = len(dataset_train)
num_data_val = len(dataset_val)

num_batch_train = np.ceil(num_data_train / batch_size)
num_batch_val = np.ceil(num_data_val / batch_size)



## ???????????? ????????????
net = UNet(nch=nch, nker=nker, learning_type=learning_type).to(device)


## ???????????? ????????????
# fn_loss = nn.BCEWithLogitsLoss().to(device)
fn_loss = nn.MSELoss().to(device)


## Optimizer ????????????
# adam optimizer??????
optim = torch.optim.Adam(net.parameters(), lr=lr)


## ????????? ???????????? functions ????????????
# output??? ???????????? ?????? ????????? ????????? ?????????


# tensor?????? numpy??? ???????????? ??????
fn_tonumpy = lambda x: x.to('cpu').detach().numpy().transpose(0, 2, 3, 1)
# normalize??? data??? ????????? denomalization????????? ??????
fn_denorm = lambda x, mean, std: (x * std) + mean
# ???????????? output??? ???????????? binary class??? ??????????????? ??????
fn_class = lambda x: 1.0 * (x > 0.5)

cmap = None


## Tensorboard ??? ???????????? ?????? SummaryWriter ??????
writer_train = SummaryWriter(log_dir=os.path.join(log_dir, 'train'))
writer_val: SummaryWriter = SummaryWriter(log_dir=os.path.join(log_dir, 'val'))


## ???????????? ???????????????
# training??? ???????????? epoch??? ????????? 0?????? ??????
st_epoch = 0


# TRAIN 
if train_continue == "on":
    net, optim, st_epoch = load(ckpt_dir=ckpt_dir, net=net, optim=optim)
    #????????? ????????? ??? network??? ????????? ??????????????? ???????????? ?????? ???????????? ??????


# training??? ????????? network??? ?????????
for epoch in range(st_epoch + 1, num_epoch + 1):
    net.train()
    loss_mse = []


    # network??? input??? ?????? output??? ???????????? forward pass
    for batch, data in enumerate(loader_train, 1):
        # forward pass
        label = data['img'].to(device)
        noise = data['noise'].to(device)

        model_input = label + noise
        input = torch.clamp(model_input, 0, 1)

        #normalization
        input = (input - 0.5) / 0.5
        label = (label - 0.5) / 0.5

        output = net(input)


        # backpropagation??? ?????? ??????
        # backward pass
        optim.zero_grad()

        loss = fn_loss(output, label)
        loss.backward()

        optim.step()

        # ???????????? ??????
        loss_mse += [loss.item()]

        print("TRAIN: EPOCH %04d / %04d | BATCH %04d / %04d | LOSS %.4f | ACCURACY %.4f" %
              (epoch, num_epoch, batch, num_batch_train, np.mean(loss_mse), 1-np.mean(loss_mse)))

        if batch % 10 == 0:
          # Tensorboard ????????????
          # Tensorboard??? input, output, label??? ??????
          label = fn_tonumpy(fn_denorm(label, mean=0.5, std=0.5))
          input = fn_tonumpy(fn_denorm(input, mean=0.5, std=0.5))
          output = fn_tonumpy(fn_denorm(output, mean=0.5, std=0.5))

          input = np.clip(input, a_min=0, a_max=1)
          output = np.clip(output, a_min=0, a_max=1)

          id = num_batch_train * (epoch - 1) + batch

          plt.imsave(os.path.join(result_dir_train, 'png', '%04d_label.png' % id), label[0].squeeze(), cmap=cmap)
          plt.imsave(os.path.join(result_dir_train, 'png', '%04d_input.png' % id), input[0].squeeze(), cmap=cmap)
          plt.imsave(os.path.join(result_dir_train, 'png', '%04d_output.png' % id), output[0].squeeze(), cmap=cmap)


    # loss ??? tensorboard??? ??????
    writer_train.add_scalar('loss', np.mean(loss_mse), epoch)
    
#=============================================================================??????????????? training?????? ?????? ???
    # network validation?????? ??????
    # validatoin????????? backpropagation??? ????????? ?????? ????????? ?????? ?????? torch.no_grad()??? activate ?????????.
    # network?????? ?????? validatoin????????? ?????? ????????? ?????? net.eval() ?????????
    with torch.no_grad():
        net.eval()
        loss_mse = []

        # training??? ??????????????? forward pass??????
        for batch, data in enumerate(loader_val, 1):
            # forward pass
            label = data['img'].to(device)
            noise = data['noise'].to(device)

            model_input = label + noise
            input = torch.clamp(model_input, 0, 1)

            #normalization
            input = (input - 0.5) / 0.5
            label = (label - 0.5) / 0.5


            output = net(input)


            # ???????????? ????????????
            loss = fn_loss(output, label)

            loss_mse += [loss.item()]

            print("VALID: EPOCH %04d / %04d | BATCH %04d / %04d | LOSS %.4f | ACCURACY %.4f" %
                  (epoch, num_epoch, batch, num_batch_val, np.mean(loss_mse), 1-np.mean(loss_mse)))

            if batch % 3 == 0:
              # Tensorboard ????????????
              label = fn_tonumpy(fn_denorm(label, mean=0.5, std=0.5))
              input = fn_tonumpy(fn_denorm(input, mean=0.5, std=0.5))
              output = fn_tonumpy(fn_denorm(output, mean=0.5, std=0.5))

              input = np.clip(input, a_min=0, a_max=1)
              output = np.clip(output, a_min=0, a_max=1)

              id = num_batch_val * (epoch - 1) + batch

              #????????? png????????? ??????
              plt.imsave(os.path.join(result_dir_val, 'png', '%04d_label.png' % id), label[0].squeeze(), cmap=cmap)
              plt.imsave(os.path.join(result_dir_val, 'png', '%04d_input.png' % id), input[0].squeeze(), cmap=cmap)
              plt.imsave(os.path.join(result_dir_val, 'png', '%04d_output.png' % id), output[0].squeeze(), cmap=cmap)


    writer_val.add_scalar('loss', np.mean(loss_mse), epoch)

    # 20????????? ????????? network??????
    if epoch % 20 == 0:
      # epoch??? ?????? ??? ????????? network??????
        save(ckpt_dir=ckpt_dir, net=net, optim=optim, epoch=epoch)

writer_train.close()
writer_val.close()

"""# Test"""

import argparse

import os
import numpy as np

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter


import matplotlib.pyplot as plt

from torchvision import transforms

ckpt_dir = "/content/drive/MyDrive/Multimedia/Termproject/checkpoint/"


## ???????????? ????????????
result_dir_test = os.path.join(result_dir, 'test')
if not os.path.exists(result_dir):
    os.makedirs(os.path.join(result_dir_test, 'png'))
    os.makedirs(os.path.join(result_dir_test, 'numpy'))


dataset_test = NoiseDataset(root_path, 128) #128??? size
dataset_test.set_mode("testing")
loader_test = DataLoader(dataset_test, batch_size=batch_size, shuffle=False)


# ????????? ???????????? variables ????????????
num_data_test = len(dataset_test)
num_batch_test = np.ceil(num_data_test / batch_size)


## ???????????? ????????????
# fn_loss = nn.BCEWithLogitsLoss().to(device)
fn_loss = nn.MSELoss().to(device)


## ???????????? ????????????
net = UNet(nch=nch, nker=nker, learning_type=learning_type).to(device)


## Optimizer ????????????
# adam optimizer??????
optim = torch.optim.Adam(net.parameters(), lr=lr)


## ????????? ???????????? functions ????????????
# output??? ???????????? ?????? ????????? ????????? ?????????


# tensor?????? numpy??? ???????????? ??????
fn_tonumpy = lambda x: x.to('cpu').detach().numpy().transpose(0, 2, 3, 1)
# normalize??? data??? ????????? denomalization????????? ??????
fn_denorm = lambda x, mean, std: (x * std) + mean
# ???????????? output??? ???????????? binary class??? ??????????????? ??????
fn_class = lambda x: 1.0 * (x > 0.5)

cmap = None

net, optim, st_epoch = load(ckpt_dir=ckpt_dir, net=net, optim=optim)


# backpropagation??? ????????? ?????? ????????? ?????? ?????? torch.no_grad()??? activate ?????????.
# network?????? ?????? validatoin????????? ?????? ????????? ?????? net.eval() ?????????
with torch.no_grad():
    net.eval()
    loss_mse = []

    for batch, data in enumerate(loader_test, 1):
        # forward pass
        input = data['img'].to(device)

        #normalization
        input = (input - 0.5) / 0.5

        output = net(input)


        print("TEST: BATCH %04d / %04d" %
              (batch, num_batch_test))
        

        # Tensorboard ????????????
        input = fn_tonumpy(fn_denorm(input, mean=0.5, std=0.5))
        output = fn_tonumpy(fn_denorm(output, mean=0.5, std=0.5))

        for j in range(label.shape[0]):
            id = batch_size * (batch - 1) + j

            input_ = input[j]
            output_ = output[j]

            # ????????? png????????? ?????????
            input_ = np.clip(input_, a_min=0, a_max=1)
            output_ = np.clip(output_, a_min=0, a_max=1)

            plt.imsave(os.path.join(result_dir_test, 'png', '%04d_input.png' % id), input_, cmap=cmap)
            plt.imsave(os.path.join(result_dir_test, 'png', '%04d_output.png' % id), output_, cmap=cmap)