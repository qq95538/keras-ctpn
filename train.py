# -*- coding: utf-8 -*-
"""
   File Name：     train
   Description :   ctpn训练
   Author :       mick.yi
   date：          2019/3/14
"""
import os
import tensorflow as tf
import keras
import numpy as np
from keras.callbacks import TensorBoard, ModelCheckpoint, ReduceLROnPlateau
from ctpn.layers import models
from ctpn.config import cur_config as config
from ctpn.utils import file_utils
from ctpn.utils.generator import generator
from ctpn.preprocess import reader


def set_gpu_growth():
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    cfg = tf.ConfigProto()
    cfg.gpu_options.allow_growth = True
    session = tf.Session(config=cfg)
    keras.backend.set_session(session)

def get_call_back():
    """
    定义call back
    :return:
    """
    checkpoint = ModelCheckpoint(filepath='/tmp/ctpn.{epoch:03d}.h5',
                                 monitor='acc',
                                 verbose=1,
                                 save_best_only=False,
                                 period=5)

    # 验证误差没有提升
    lr_reducer = ReduceLROnPlateau(monitor='loss',
                                   factor=np.sqrt(0.1),
                                   cooldown=1,
                                   patience=1,
                                   min_lr=0)
    log = TensorBoard(log_dir='log')
    return [lr_reducer, checkpoint, log]


def main():
    set_gpu_growth()
    # 加载标注
    annotation_files = file_utils.get_sub_files(config.IMAGE_GT_DIR)
    image_annotations = [reader.load_annotation(file,
                                                config.IMAGE_DIR) for file in annotation_files]
    # 加载模型
    m = models.ctpn_net(config, 'train')
    models.compile(m, config, loss_names=['ctpn_regress_loss', 'ctpn_class_loss'])
    m.summary()
    # 生成器
    gen = generator(image_annotations, config.IMAGE_SHAPE[0], config.MAX_GT_INSTANCES, config.IMAGES_PER_GPU)

    # 训练
    m.fit_generator(gen,
                    steps_per_epoch=len(image_annotations) // config.IMAGES_PER_GPU,
                    epochs=50,
                    verbose=True,
                    callbacks=get_call_back(),
                    use_multiprocessing=True)

    # 保存模型
    m.save(config.WEIGHT_PATH)
    # i = 0
    # while i < 10000:
    #     data = next(gen)
    #     if data[0]["gt_boxes"].shape != (2, 200, 5):
    #         print(data[0]["gt_boxes"][0].shape, data[0]["gt_boxes"][1].shape)
    #     i += 1
    #     import time
    #     if i % 100 == 0:
    #         print("{}:{}".format(time.time(), i))


if __name__ == '__main__':
    main()