# -*- coding: utf-8 -*-
"""
Created on Tue Jul 23 12:09:08 2019

trainer

@author: tadahaya
"""
import torch

from .utils import save_experiment, save_checkpoint

class Trainer:
    def __init__(self, config, model, optimizer, loss_fn, exp_name, device):
        self.config = config
        self.model = model.to(device)
        self.optimizer = optimizer
        self.loss_fn = loss_fn
        self.exp_name = exp_name
        self.device = device


    def train(self, trainloader, testloader, save_model_evry_n_epochs=0):
        """
        train the model for the specified number of epochs.
        
        """
        # configの確認
        config = self.config
        assert config["hidden_size"] % config["num_attention_heads"] == 0
        assert config["intermediate_size"] == 4 * config["hidden_size"]
        assert config["image_size"] % config["patch_size"] == 0
        # keep track of the losses and accuracies
        train_losses, test_losses, accuracies = [], [], []
        # training
        for i in range(config["epochs"]):
            train_loss = self.train_epoch(trainloader)
            accuracy, test_loss = self.evaluate(testloader)
            train_losses.append(train_loss)
            test_losses.append(test_loss)
            print(
                f"Epoch: {i + 1}, Train_loss: {train_loss:.4f}, Test loss: {test_loss:.4f}, Accuracy: {accuracy:.4f}"
                )
            if save_model_evry_n_epochs > 0 and (i + 1) % save_model_evry_n_epochs == 0 and i + 1 != config["epochs"]:
                print("> Save checkpoint at epoch", i + 1)
                save_checkpoint(self.exp_name, self.model, i + 1)
        # save the experiment
        save_experiment(
            self.exp_name, config, self.model, train_losses, test_losses, accuracies
            )
        # ToDo base_dirを追加


    def train_epoch(self, trainloader):
        """ train the model for one epoch """
        self.model.train()
        total_loss = 0
        for y1, y2 in trainloader:
            # batchをdeviceへ
            y1, y2 = y1.to(self.device), y2.to(self.device)
            # 勾配を初期化
            self.optimizer.zero_grad()
            # forward / loss
            loss = self.model(y1, y2)[0] # attentionもNoneで返るので
            # backpropagation
            loss.backward()
            # パラメータ更新
            self.optimizer.step()
            total_loss += loss.item()
        return total_loss / len(trainloader.dataset) # 全データセットのうちのいくらかという比率になっている
    

    @torch.no_grad()
    def evaluate(self, testloader):
        self.model.eval()
        total_loss = 0
        correct = 0
        with torch.no_grad():
            for y1, y2 in testloader:
                # batchをdeviceへ
                y1, y2 = y1.to(self.device), y2.to(self.device)
                # loss
                loss, _ = self.model(y1, y2)
                total_loss += loss.item()
        accuracy = correct / len(testloader.dataset)
        avg_loss = total_loss / len(testloader.dataset)
        return accuracy, avg_loss