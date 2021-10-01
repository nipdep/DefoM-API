
import unittest
from unittest.mock import patch, Mock

from tensorflow.python.util import object_identity
import numpy as np

from defom.src.DLClient import ClassiModel


class DLClassTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('### Setting up DL classi model ###')
        super(DLClassTest, cls).setUpClass()
        cls.model = ClassiModel.getInstance()

    def tearDown(self):
        ...

    def setUp(self):
        ...

    def test_singelton(self):
        model_1 = ClassiModel.getInstance()
        self.assertTrue(model_1 is self.model)

    def count_params(self, weights):
        return int(sum(np.prod(p.shape.as_list()) for p in object_identity.ObjectIdentitySet(weights)))

    def test_trainable_params(self):
        trainable_cnt = self.count_params(self.model.model.trainable_weights)
        self.assertEqual(trainable_cnt, 0)

    def test_model_functions(self):
        tensor_shape = [10]+list(self.model.image_shape)
        sample_input = np.zeros(tensor_shape)
        output = self.model.model.predict(sample_input)
        self.assertEqual(10, output.shape[0])
        self.assertEqual(8, output.shape[1])

    def test_output_classes(self):
        tensor_shape = [10]+list(self.model.image_shape)
        sample_input = np.random.random(tensor_shape)
        inf_classes = self.model.inference(sample_input)
        self.assertTrue(all(i in self.model.label_dict.values() for i in inf_classes[0]))
        self.assertEqual(10, len(inf_classes))

    def test_image_preprocess(self):
        tensor_shape = (10,224, 224, 3)
        sample_input = np.random.random(tensor_shape)*2500
        prep_image = self.model.preprocess_resize(sample_input)
        self.assertEqual(prep_image.shape, (10, 128, 128, 3))
        self.assertTrue(np.max(prep_image) <= 1)
        self.assertTrue(np.min(prep_image) >= 0)
    

# if __name__ == '__main__':
#     unittest.main()