# -*- coding: utf-8 -*-
# pylint: skip-file

import unittest
from nose.tools import eq_, ok_
from mock import patch
import numpy as np
from PIL import Image
import torch
from torchvision import transforms

from modules.dataset_indexing.pytorch import PoseDataset
from modules.dataset_indexing.pytorch import Crop, RandomNoise, Scale


class TestPoseDatasetConstructure(unittest.TestCase):

    @patch('modules.dataset_indexing.pytorch.pose_dataset.open')
    def test_load_dataset(self, mock):
        # prepare mock.
        mock.return_value = ['image1.png,10.0,20.0,0.0,30.0,40.0,1.0\n',
                             'image2.png,50.0,60.0,1.0,70.0,80.0,0.0\n']
        # test.
        dataset = PoseDataset('test_data')
        eq_(dataset.images, ['image1.png', 'image2.png'])
        correct = [np.array([[10, 20], [30, 40]], dtype=np.float32),
                   np.array([[50, 60], [70, 80]], dtype=np.float32)]
        for p, c in zip(dataset.poses, correct):
            ok_((p == c).all())
        correct = [np.array([[0], [1]], dtype=np.int32),
                   np.array([[1], [0]], dtype = np.int32)]
        for v, c in zip(dataset.visibilities, correct):
            ok_((v == c).all())

class TestPoseDataset(unittest.TestCase):

    @patch('modules.dataset_indexing.pytorch.pose_dataset.open')
    def setUp(self, mock):
        # prepare mock.
        mock.return_value = ['image1.png,108.0,50.0,1.0,148.0,180.0,0.0,148.0,180.0,1.0\n',
                             'image2.png,40.0,50.0,1.0,160.0,180.0,1.0,160.0,180.0,0.0\n']
        # set up.
        self.path = 'test_data'
        self.dataset = PoseDataset(self.path)

    @patch('PIL.Image.open', return_value=Image.new('RGB', (320, 240)))
    def test_read_image(self, mock):
        image = self.dataset._read_image('dummy.png')
        eq_(type(image), Image.Image)
        eq_(image.size, (320, 240))
        eq_(image.mode, 'RGB')

    def test_len(self):
        eq_(len(self.dataset), 2)

    @patch('PIL.Image.open')
    def test_getitem(self, mock):
        # prepare mock.
        shape = (256, 256)
        mock.side_effect = [Image.new('RGB', shape),
                            Image.new('RGB', shape)]
        # test.
        image, pose, visibility = self.dataset[0]
        eq_(type(image), Image.Image)
        eq_(image.size, (256, 256))
        eq_(image.mode, 'RGB')
        eq_(pose.dtype, np.float32)
        ok_((pose == np.array([[108, 50], [148, 180], [148, 180]])).all())
        eq_(visibility.dtype, np.int32)
        ok_((visibility == np.array([[1], [0], [1]])).all())
        image, pose, visibility = self.dataset[1]
        eq_(type(image), Image.Image)
        eq_(image.size, (256, 256))
        eq_(image.mode, 'RGB')
        eq_(pose.dtype, np.float32)
        ok_((pose == np.array([[40, 50], [160, 180], [160, 180]])).all())
        eq_(visibility.dtype, np.int32)
        ok_((visibility == np.array([[1], [1], [0]])).all())

class TestPoseDatasetWithTransform(unittest.TestCase):

    @patch('modules.dataset_indexing.pytorch.pose_dataset.open')
    def setUp(self, mock):
        # prepare mock.
        mock.return_value = ['image1.png,108.0,50.0,1.0,148.0,180.0,0.0,148.0,180.0,1.0\n',
                             'image2.png,40.0,50.0,1.0,160.0,180.0,1.0,160.0,180.0,0.0\n']
        # set up.
        self.path = 'test_data'
        self.dataset = PoseDataset(
            self.path,
            input_transform=transforms.Compose([
                transforms.ToTensor()]),
            output_transform=Scale(),
            transform=Crop(data_augmentation=False))

    @patch('PIL.Image.open')
    def test_getitem(self, mock):
        # prepare mock.
        shape = (256, 256)
        mock.side_effect = [Image.new('RGB', shape),
                            Image.new('RGB', shape)]
        # test.
        image, pose, visibility = self.dataset[0]
        eq_(type(image), torch.FloatTensor)
        eq_(image.size(), (3, 227, 227))
        eq_(pose.dtype, np.float32)
        ok_(np.linalg.norm(pose - np.array([[94., 49.], [134., 179.], [134., 179.]])/227) < 1.e-5)
        eq_(visibility.dtype, np.int32)
        ok_((visibility == np.array([[1], [0], [1]])).all())
        image, pose, visibility = self.dataset[1]
        eq_(type(image), torch.FloatTensor)
        eq_(image.size(), (3, 227, 227))
        ok_(np.linalg.norm(pose - np.array([[40., 49.], [160., 179.], [160., 179.]])/227) < 1.e-5)
        eq_(visibility.dtype, np.int32)
        ok_((visibility == np.array([[1], [1], [0]])).all())

class TestPoseDatasetWithTransformDataAugmentation(unittest.TestCase):

    @patch('modules.dataset_indexing.pytorch.pose_dataset.open')
    def setUp(self, mock):
        # prepare mock.
        mock.return_value = ['image1.png,108.0,50.0,1.0,148.0,180.0,0.0,148.0,180.0,1.0\n',
                             'image2.png,40.0,50.0,1.0,160.0,180.0,1.0,160.0,180.0,0.0\n']
        # set up.
        self.path = 'test_data'
        self.dataset = PoseDataset(
            self.path,
            input_transform=transforms.Compose([
                transforms.ToTensor(),
                RandomNoise()]),
            output_transform=Scale(),
            transform=Crop(data_augmentation=True))

    @patch('PIL.Image.open')
    def test_getitem(self, mock):
        # prepare mock.
        shape = (256, 256)
        mock.side_effect = [Image.new('RGB', shape),
                            Image.new('RGB', shape)]
        # test.
        for i in range(len(self.dataset)):
            image, pose, visibility = self.dataset[i]
            eq_(type(image), torch.FloatTensor)
            eq_(image.size(), (3, 227, 227))
            ok_((image >= 0).all())
            ok_((image <= 1).all())
            eq_(pose.dtype, np.float32)
            ok_((pose >= 0).all())
            ok_((pose <= 1).all())
            eq_(visibility.dtype, np.int32)
            eq_(visibility.shape, (3, 1))
