import unittest
from unittest.mock import patch, Mock

from tensorflow.python.util import object_identity
import numpy as np

from defom.src.DLClient import MaskModel


class DLMaskTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('### Setting up DL Mask model ###')
        super(DLMaskTest, cls).setUpClass()
        cls.model = MaskModel.getInstance()

    def tearDown(self):
        ...

    def setUp(self):
        ...

    def test_singelton(self):
        model_1 = MaskModel.getInstance()
        self.assertTrue(model_1 is self.model)

    def count_params(self, weights):
        return int(sum(np.prod(p.shape.as_list()) for p in object_identity.ObjectIdentitySet(weights)))

    def test_trainable_params(self):
        trainable_cnt = self.count_params(self.model.model.trainable_weights)
        self.assertEqual(trainable_cnt, 0)

    def test_model_functions(self):
        tensor_shape = [10]+list(self.model.image_shape)
        output_shape = tensor_shape[1:3]+[1]
        sample_input = np.zeros(tensor_shape)
        output = self.model.model.predict(sample_input)
        self.assertEqual(10, output.shape[0])
        self.assertEqual(output_shape, list(output.shape[1:]))

    def test_output_classes(self):
        tensor_shape = [10]+list(self.model.image_shape)
        output_shape = tensor_shape[1:3]+[1]
        sample_input = np.random.random(tensor_shape)
        inf_mask = self.model.inference(sample_input)

        self.assertTrue(1, inf_mask.shape[-1])
        self.assertEqual(10, len(inf_mask))

        uni_values = list(np.unique(inf_mask))
        self.assertEqual([0,1], uni_values)

    def test_image_preprocess(self):
        tensor_shape = (10,224, 224, 3)
        sample_input = np.random.random(tensor_shape)*2500
        prep_image = self.model.preprocess_resize(sample_input)
        self.assertEqual(prep_image.shape, (10, 128, 128, 3))
        self.assertTrue(np.max(prep_image) <= 1)
        self.assertTrue(np.min(prep_image) >= 0)
    