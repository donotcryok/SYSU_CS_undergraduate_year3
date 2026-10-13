from builtins import object
import numpy as np

from ..layers import *
from ..fast_layers import *
from ..layer_utils import *


class ThreeLayerConvNet(object):
    """
    A three-layer convolutional network with the following architecture:

    conv - relu - 2x2 pool - affine - relu - affine - softmax

    The network operates on minibatches of data that have shape (N, C, H, W)
    consisting of N images, each with height H and width W and with C input
    channels.
    """

    def __init__(
        self,
        input_dim=(3, 32, 32),
        num_filters=32,
        filter_size=7,
        hidden_dim=100,
        num_classes=10,
        weight_scale=1e-3,
        reg=0.0,
        pooling='maxpool',
        dtype=np.float32,
    ):
        """
        Initialize a new network.

        Inputs:
        - input_dim: Tuple (C, H, W) giving size of input data
        - num_filters: Number of filters to use in the convolutional layer
        - filter_size: Width/height of filters to use in the convolutional layer
        - hidden_dim: Number of units to use in the fully-connected hidden layer
        - num_classes: Number of scores to produce from the final affine layer.
        - weight_scale: Scalar giving standard deviation for random initialization
          of weights.
        - reg: Scalar giving L2 regularization strength
        - dtype: numpy datatype to use for computation.
        - pooling: What type of pooling the network should use. Valid values are
          "maxpool" or "avgpool"
        """
        self.params = {}
        self.reg = reg
        self.dtype = dtype
        self.pooling = pooling

        ############################################################################
        # TODO: Initialize weights and biases for the three-layer convolutional    #
        # network. Weights should be initialized from a Gaussian centered at 0.0   #
        # with standard deviation equal to weight_scale; biases should be          #
        # initialized to zero. All weights and biases should be stored in the      #
        #  dictionary self.params. Store weights and biases for the convolutional  #
        # layer using the keys 'W1' and 'b1'; use keys 'W2' and 'b2' for the       #
        # weights and biases of the hidden affine layer, and keys 'W3' and 'b3'    #
        # for the weights and biases of the output affine layer.                   #
        #                                                                          #
        # IMPORTANT: For this assignment, you can assume that the padding          #
        # and stride of the first convolutional layer are chosen so that           #
        # **the width and height of the input are preserved**. Take a look at      #
        # the start of the loss() function to see how that happens.                #
        ############################################################################
        # *****START OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)*****

        # 解析输入维度
        C, H, W = input_dim
        
        # 第一层: 卷积层
        # W1: (num_filters, C, filter_size, filter_size)
        self.params['W1'] = np.random.randn(num_filters, C, filter_size, filter_size) * weight_scale
        self.params['b1'] = np.zeros(num_filters)
        
        # 计算池化后的尺寸 (2x2 pool with stride 2)
        H_pool = H // 2
        W_pool = W // 2
        
        # 第二层: 隐藏全连接层
        # 输入尺寸: num_filters * H_pool * W_pool
        self.params['W2'] = np.random.randn(num_filters * H_pool * W_pool, hidden_dim) * weight_scale
        self.params['b2'] = np.zeros(hidden_dim)
        
        # 第三层: 输出全连接层
        self.params['W3'] = np.random.randn(hidden_dim, num_classes) * weight_scale
        self.params['b3'] = np.zeros(num_classes)

        # *****END OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)*****
        ############################################################################
        #                             END OF YOUR CODE                             #
        ############################################################################

        for k, v in self.params.items():
            self.params[k] = v.astype(dtype)

    def loss(self, X, y=None):
        """
        Evaluate loss and gradient for the three-layer convolutional network.

        Input / output: Same API as TwoLayerNet in fc_net.py.
        """
        W1, b1 = self.params["W1"], self.params["b1"]
        W2, b2 = self.params["W2"], self.params["b2"]
        W3, b3 = self.params["W3"], self.params["b3"]

        # pass conv_param to the forward pass for the convolutional layer
        # Padding and stride chosen to preserve the input spatial size
        filter_size = W1.shape[2]
        conv_param = {"stride": 1, "pad": (filter_size - 1) // 2}

        # pass pool_param to the forward pass for the max-pooling layer
        pool_param = {"pool_height": 2, "pool_width": 2, "stride": 2}

        scores = None
        ############################################################################
        # TODO: Implement the forward pass for the three-layer convolutional net,  #
        # computing the class scores for X and storing them in the scores          #
        # variable.                                                                #
        #                                                                          #
        # Remember you can use the functions defined in annp/fast_layers.py and  #
        # annp/layer_utils.py in your implementation (already imported).         #
        ############################################################################
        # *****START OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)*****

        # 前向传播: conv - relu - pool - affine - relu - affine
        
        # 第一层: conv - relu - pool
        if self.pooling == 'maxpool':
            out1, cache1 = conv_relu_maxpool_forward(X, W1, b1, conv_param, pool_param)
        else:  # avgpool
            # 需要手动实现 conv - relu - avgpool
            out_conv, cache_conv = conv_relu_forward(X, W1, b1, conv_param)
            out1, cache_pool = avg_pool_forward_naive(out_conv, pool_param)
            cache1 = (cache_conv, cache_pool)
        
        # 第二层: affine - relu
        out2, cache2 = affine_relu_forward(out1, W2, b2)
        
        # 第三层: affine (输出层)
        scores, cache3 = affine_forward(out2, W3, b3)

        # *****END OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)*****
        ############################################################################
        #                             END OF YOUR CODE                             #
        ############################################################################

        if y is None:
            return scores

        loss, grads = 0, {}
        ############################################################################
        # TODO: Implement the backward pass for the three-layer convolutional net, #
        # storing the loss and gradients in the loss and grads variables. Compute  #
        # data loss using softmax, and make sure that grads[k] holds the gradients #
        # for self.params[k]. Don't forget to add L2 regularization!               #
        #                                                                          #
        # NOTE: To ensure that your implementation matches ours and you pass the   #
        # automated tests, make sure that your L2 regularization includes a factor #
        # of 0.5 to simplify the expression for the gradient.                      #
        ############################################################################
        # *****START OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)*****

        # 计算 softmax loss 和梯度
        loss, dscores = softmax_loss(scores, y)
        
        # 添加 L2 正则化
        loss += 0.5 * self.reg * (np.sum(W1 ** 2) + np.sum(W2 ** 2) + np.sum(W3 ** 2))
        
        # 反向传播
        # 第三层反向传播
        dout2, grads['W3'], grads['b3'] = affine_backward(dscores, cache3)
        grads['W3'] += self.reg * W3
        
        # 第二层反向传播
        dout1, grads['W2'], grads['b2'] = affine_relu_backward(dout2, cache2)
        grads['W2'] += self.reg * W2
        
        # 第一层反向传播
        if self.pooling == 'maxpool':
            dx, grads['W1'], grads['b1'] = conv_relu_maxpool_backward(dout1, cache1)
        else:  # avgpool
            cache_conv, cache_pool = cache1
            dpool = avg_pool_backward_naive(dout1, cache_pool)
            dx, grads['W1'], grads['b1'] = conv_relu_backward(dpool, cache_conv)
        grads['W1'] += self.reg * W1

        # *****END OF YOUR CODE (DO NOT DELETE/MODIFY THIS LINE)*****
        ############################################################################
        #                             END OF YOUR CODE                             #
        ############################################################################

        return loss, grads


class DeepConvNet(object):
    """
    A deep convolutional network for CIFAR-10 classification.
    
    Architecture:
    [conv - bn - relu] x 2 -> pool -> [conv - bn - relu] x 2 -> pool ->
    [affine - bn - relu] -> [affine] -> softmax
    
    This architecture is inspired by VGG-style networks with:
    - Small 3x3 filters throughout
    - Batch normalization after each conv/affine layer
    - Max pooling to reduce spatial dimensions
    - Two fully connected layers at the end
    """
    
    def __init__(
        self,
        input_dim=(3, 32, 32),
        num_filters=[32, 32, 64, 64],
        filter_size=3,
        hidden_dim=512,
        num_classes=10,
        weight_scale=1e-2,
        reg=0.0,
        use_batchnorm=True,
        dropout=0.5,
        dtype=np.float32,
        seed=None,
    ):
        """
        Initialize a new DeepConvNet.
        
        Inputs:
        - input_dim: Tuple (C, H, W) giving size of input data
        - num_filters: List of number of filters for each conv layer
        - filter_size: Size of convolutional filters (assumed square)
        - hidden_dim: Number of units in the hidden affine layer
        - num_classes: Number of classes to classify
        - weight_scale: Standard deviation for random initialization
        - reg: L2 regularization strength
        - use_batchnorm: Whether to use batch normalization
        - dropout: Dropout probability (0 means no dropout)
        - dtype: numpy datatype for computation
        - seed: Random seed for reproducibility
        """
        self.use_batchnorm = use_batchnorm
        self.use_dropout = dropout > 0
        self.reg = reg
        self.num_layers = len(num_filters) + 2  # conv layers + 2 affine layers
        self.dtype = dtype
        self.params = {}
        
        C, H, W = input_dim
        
        # Initialize convolutional layers
        # Architecture: [conv-bn-relu] x 2 -> pool -> [conv-bn-relu] x 2 -> pool
        # After first pool: H/2, W/2
        # After second pool: H/4, W/4
        
        # Layer 1: conv (C -> num_filters[0])
        self.params['W1'] = np.random.randn(num_filters[0], C, filter_size, filter_size) * weight_scale
        self.params['b1'] = np.zeros(num_filters[0])
        
        # Layer 2: conv (num_filters[0] -> num_filters[1])
        self.params['W2'] = np.random.randn(num_filters[1], num_filters[0], filter_size, filter_size) * weight_scale
        self.params['b2'] = np.zeros(num_filters[1])
        
        # After first pool: H//2, W//2
        H1, W1 = H // 2, W // 2
        
        # Layer 3: conv (num_filters[1] -> num_filters[2])
        self.params['W3'] = np.random.randn(num_filters[2], num_filters[1], filter_size, filter_size) * weight_scale
        self.params['b3'] = np.zeros(num_filters[2])
        
        # Layer 4: conv (num_filters[2] -> num_filters[3])
        self.params['W4'] = np.random.randn(num_filters[3], num_filters[2], filter_size, filter_size) * weight_scale
        self.params['b4'] = np.zeros(num_filters[3])
        
        # After second pool: H//4, W//4
        H2, W2 = H // 4, W // 4
        
        # Initialize batch norm parameters for conv layers
        if use_batchnorm:
            for i in range(1, 5):
                self.params['gamma' + str(i)] = np.ones(num_filters[i-1])
                self.params['beta' + str(i)] = np.zeros(num_filters[i-1])
        
        # Layer 5: affine (num_filters[3] * H2 * W2 -> hidden_dim)
        fc1_input_dim = num_filters[3] * H2 * W2
        self.params['W5'] = np.random.randn(fc1_input_dim, hidden_dim) * weight_scale
        self.params['b5'] = np.zeros(hidden_dim)
        
        if use_batchnorm:
            self.params['gamma5'] = np.ones(hidden_dim)
            self.params['beta5'] = np.zeros(hidden_dim)
        
        # Layer 6: affine (hidden_dim -> num_classes)
        self.params['W6'] = np.random.randn(hidden_dim, num_classes) * weight_scale
        self.params['b6'] = np.zeros(num_classes)
        
        # Initialize batch norm parameters
        self.bn_params = []
        if use_batchnorm:
            self.bn_params = [{'mode': 'train'} for _ in range(5)]  # 4 conv + 1 fc
        
        # Initialize dropout parameters
        self.dropout_param = {}
        if self.use_dropout:
            self.dropout_param = {'mode': 'train', 'p': dropout}
            if seed is not None:
                self.dropout_param['seed'] = seed
        
        # Cast all parameters to correct dtype
        for k, v in self.params.items():
            self.params[k] = v.astype(dtype)
    
    def loss(self, X, y=None):
        """
        Evaluate loss and gradient for the deep convolutional network.
        """
        X = X.astype(self.dtype)
        mode = 'test' if y is None else 'train'
        
        # Set mode for batchnorm and dropout
        if self.use_batchnorm:
            for bn_param in self.bn_params:
                bn_param['mode'] = mode
        if self.use_dropout:
            self.dropout_param['mode'] = mode
        
        # Conv parameters
        filter_size = self.params['W1'].shape[2]
        conv_param = {'stride': 1, 'pad': (filter_size - 1) // 2}
        pool_param = {'pool_height': 2, 'pool_width': 2, 'stride': 2}
        
        # Forward pass
        caches = []
        out = X
        
        # Layer 1: conv - bn - relu
        W1, b1 = self.params['W1'], self.params['b1']
        if self.use_batchnorm:
            gamma1, beta1 = self.params['gamma1'], self.params['beta1']
            out, cache = conv_bn_relu_forward(out, W1, b1, gamma1, beta1, conv_param, self.bn_params[0])
        else:
            out, cache = conv_relu_forward(out, W1, b1, conv_param)
        caches.append(cache)
        
        # Layer 2: conv - bn - relu
        W2, b2 = self.params['W2'], self.params['b2']
        if self.use_batchnorm:
            gamma2, beta2 = self.params['gamma2'], self.params['beta2']
            out, cache = conv_bn_relu_forward(out, W2, b2, gamma2, beta2, conv_param, self.bn_params[1])
        else:
            out, cache = conv_relu_forward(out, W2, b2, conv_param)
        caches.append(cache)
        
        # Pool 1
        out, cache = max_pool_forward_fast(out, pool_param)
        caches.append(cache)
        
        # Layer 3: conv - bn - relu
        W3, b3 = self.params['W3'], self.params['b3']
        if self.use_batchnorm:
            gamma3, beta3 = self.params['gamma3'], self.params['beta3']
            out, cache = conv_bn_relu_forward(out, W3, b3, gamma3, beta3, conv_param, self.bn_params[2])
        else:
            out, cache = conv_relu_forward(out, W3, b3, conv_param)
        caches.append(cache)
        
        # Layer 4: conv - bn - relu
        W4, b4 = self.params['W4'], self.params['b4']
        if self.use_batchnorm:
            gamma4, beta4 = self.params['gamma4'], self.params['beta4']
            out, cache = conv_bn_relu_forward(out, W4, b4, gamma4, beta4, conv_param, self.bn_params[3])
        else:
            out, cache = conv_relu_forward(out, W4, b4, conv_param)
        caches.append(cache)
        
        # Pool 2
        out, cache = max_pool_forward_fast(out, pool_param)
        caches.append(cache)
        
        # Flatten for fully connected layers
        N = out.shape[0]
        out = out.reshape(N, -1)
        
        # Layer 5: affine - bn - relu - dropout
        W5, b5 = self.params['W5'], self.params['b5']
        if self.use_batchnorm:
            gamma5, beta5 = self.params['gamma5'], self.params['beta5']
            out, cache = affine_bn_relu_forward(out, W5, b5, gamma5, beta5, self.bn_params[4])
            caches.append(cache)
        else:
            out, cache = affine_relu_forward(out, W5, b5)
            caches.append(cache)
        
        if self.use_dropout:
            out, cache = dropout_forward(out, self.dropout_param)
            caches.append(cache)
        
        # Layer 6: affine (output)
        W6, b6 = self.params['W6'], self.params['b6']
        scores, cache = affine_forward(out, W6, b6)
        caches.append(cache)
        
        if mode == 'test':
            return scores
        
        # Backward pass
        loss, grads = 0.0, {}
        
        # Compute softmax loss
        loss, dscores = softmax_loss(scores, y)
        
        # Add L2 regularization
        for i in range(1, 7):
            W = self.params['W' + str(i)]
            loss += 0.5 * self.reg * np.sum(W ** 2)
        
        # Backward through layer 6 (affine)
        dout, grads['W6'], grads['b6'] = affine_backward(dscores, caches[-1])
        grads['W6'] += self.reg * self.params['W6']
        
        # Backward through dropout (if used)
        if self.use_dropout:
            dout = dropout_backward(dout, caches[-2])
            fc_cache_idx = -3
        else:
            fc_cache_idx = -2
        
        # Backward through layer 5 (affine - bn - relu)
        if self.use_batchnorm:
            dout, grads['W5'], grads['b5'], grads['gamma5'], grads['beta5'] = \
                affine_bn_relu_backward(dout, caches[fc_cache_idx])
        else:
            dout, grads['W5'], grads['b5'] = affine_relu_backward(dout, caches[fc_cache_idx])
        grads['W5'] += self.reg * self.params['W5']
        
        # Backward through pool 2
        dout = max_pool_backward_fast(dout, caches[-4])
        
        # Reshape dout back to conv output shape
        dout = dout.reshape(dout.shape[0], dout.shape[1], dout.shape[2], dout.shape[3])
        
        # Backward through layer 4 (conv - bn - relu)
        if self.use_batchnorm:
            dout, grads['W4'], grads['b4'], grads['gamma4'], grads['beta4'] = \
                conv_bn_relu_backward(dout, caches[-5])
        else:
            dout, grads['W4'], grads['b4'] = conv_relu_backward(dout, caches[-5])
        grads['W4'] += self.reg * self.params['W4']
        
        # Backward through layer 3 (conv - bn - relu)
        if self.use_batchnorm:
            dout, grads['W3'], grads['b3'], grads['gamma3'], grads['beta3'] = \
                conv_bn_relu_backward(dout, caches[-6])
        else:
            dout, grads['W3'], grads['b3'] = conv_relu_backward(dout, caches[-6])
        grads['W3'] += self.reg * self.params['W3']
        
        # Backward through pool 1
        dout = max_pool_backward_fast(dout, caches[-7])
        
        # Backward through layer 2 (conv - bn - relu)
        if self.use_batchnorm:
            dout, grads['W2'], grads['b2'], grads['gamma2'], grads['beta2'] = \
                conv_bn_relu_backward(dout, caches[-8])
        else:
            dout, grads['W2'], grads['b2'] = conv_relu_backward(dout, caches[-8])
        grads['W2'] += self.reg * self.params['W2']
        
        # Backward through layer 1 (conv - bn - relu)
        if self.use_batchnorm:
            dout, grads['W1'], grads['b1'], grads['gamma1'], grads['beta1'] = \
                conv_bn_relu_backward(dout, caches[-9])
        else:
            dout, grads['W1'], grads['b1'] = conv_relu_backward(dout, caches[-9])
        grads['W1'] += self.reg * self.params['W1']
        
        return loss, grads
