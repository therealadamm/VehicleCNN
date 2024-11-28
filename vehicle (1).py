# -*- coding: utf-8 -*-
"""Vehicle.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1vTQILpoJhWwEla7yeXYM9cULJ_NRYILO
"""

!curl -L -o archive.zip https://www.kaggle.com/api/v1/datasets/download/brsdincer/vehicle-detection-image-set
!unzip archive.zip

import torch
import torchvision
from torchsummary import summary

# Step 1: Dataset Preparation (no changes)
data_path = '/content/data'

# create an empty list
transform = [torchvision.transforms.Resize((256, 256)),  # Resize the image to 256x256 first
             torchvision.transforms.RandomHorizontalFlip(),
             torchvision.transforms.RandomRotation(10),
             torchvision.transforms.ToTensor(),          # Convert input image to tensor #it's 3d
             torchvision.transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])]  # Normalize the data

transformation = torchvision.transforms.Compose(transform)

full_dataset = torchvision.datasets.ImageFolder(root=data_path,
                                                transform=transformation)

# split into training and testing dataset
train_size = int(0.7 * len(full_dataset))  # 70% of data will be trained
test_size = len(full_dataset) - train_size  # 30% of data will be tested #daripada 17k images tu 30% digunakan as benchamark to evaluate
train_dataset, test_dataset = torch.utils.data.random_split(full_dataset, [train_size, test_size])

# setting up your data loader
batch_size = 32
#makin rendah makin slow, makin detail tapi possible overfitting try hard

# Train loader
train_loader = torch.utils.data.DataLoader(train_dataset,
                                           batch_size=batch_size,
                                           shuffle=True)

# Test loader
test_loader = torch.utils.data.DataLoader(test_dataset,
                                          batch_size=batch_size,
                                          shuffle=False)

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

num_epochs = 5
num_classes = 2
learning_rate = 0.001

# Step 2: Create CNN model with 2 Convolutional layers
class CNN(torch.nn.Module):
    def __init__(self, num_classes):
        super(CNN, self).__init__()

        # First convolutional layer initialization
        self.conv1 = torch.nn.Conv2d(3, 12, kernel_size=3, stride=1, padding=1) # lagi byk filter/output channel lagi molek , more information to take
        self.batch1 = torch.nn.BatchNorm2d(12) # nk reduce noise
        self.act1 = torch.nn.ReLU()
        self.drop1 = torch.nn.Dropout2d(p=0.2) # tutup randomly node
        self.pool1 = torch.nn.MaxPool2d(kernel_size=2) # kurangkan details supaya flexible dia study x memorize
        #overfitting train byk sgt

        # Second convolutional layer initialization
        self.conv2 = torch.nn.Conv2d(12, 24, kernel_size=3, stride=1, padding=1)  # Output channels = 24
        self.batch2 = torch.nn.BatchNorm2d(24)
        self.act2 = torch.nn.ReLU()
        self.drop2 = torch.nn.Dropout2d(p=0.2)
        self.pool2 = torch.nn.MaxPool2d(kernel_size=2)

        # Flatten
        self.flatten = torch.nn.Flatten() #kita nak satu 1d of matrix as answer

        # Fully connected layer
        self.fc = torch.nn.Linear(24 * 64 * 64, out_features=num_classes)  # Adjusting for second conv layer

    def forward(self, x):
        # Pass through first conv layer
        out = self.conv1(x) # out is output
        out = self.batch1(out)
        out = self.act1(out)
        out = self.drop1(out)
        out = self.pool1(out)

        # Pass through second conv layer
        #out atas tu dia masuk () bawah ni
        out = self.conv2(out)
        out = self.batch2(out)
        out = self.act2(out)
        out = self.drop2(out)
        out = self.pool2(out)

        # Flatten and fully connected layer
        out = self.flatten(out)
        out = self.fc(out)

        return torch.nn.functional.log_softmax(out, dim=1)


model = CNN(num_classes).to(device)  # Move the model to the device (GPU if available, CPU otherwise)

print(summary(model, (3, 256, 256)))

#  create test function

def test(model, test_loader, device):
    # set model to evaluation mode
    model.eval()  # Kita nak grade dia


    with torch.no_grad():
        correct = 0
        total = 0
        for images, labels in test_loader:
            images = images.to(device)
            labels = labels.to(device)
            predicted_output = model(images)
            _, predicted = torch.max(predicted_output.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item() # brpa banyak betul budak tu dapat teka

    acc = correct / total * 100
    return acc

# Train the model
criterion = torch.nn.CrossEntropyLoss() #
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)  # SDG is shit, so slow, waste my GPU, use my name

# Set the model into training mode
epoch_loss = 0
lost_list = []  # to store the losses in list
training_loss = []  # to store the epoch training loss
training_acc = []  # to store the training accuracy
epoch_num = []  # epoch number


num_epoch = 5
model.train()
total_step = len(train_loader)
for epoch in range(num_epoch):
    for i, (images, labels) in enumerate(train_loader):
        model.train()
        images = images.to(device)
        labels = torch.eye(num_classes)[labels].to(device)
        # cat jadi 01 dog 10 sbb data skrg xde label,

        # Forward pass
        outputs = model(images)
        loss = criterion(outputs, labels)

        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # to calculate the loss
        epoch_loss = epoch_loss + loss.item()

        lost_list.append(epoch_loss)

        # to print out the loss for every step
        if (i + 1) % 5000 == 0:
            print(f'Epoch [{epoch+1}/{5}], Step [{i+1}/{len(train_loader)}], Loss: {loss.item():.4f}')

    avg_loss = epoch_loss / (i + 1)
    training_loss.append(avg_loss)

    # accuracy
    accuracy = test(model, test_loader, device) # Kita nak grade
    training_acc.append(accuracy)

    epoch_num.append(epoch)
    epoch_loss = 0

#import matplotlib.pyplot as plt

plt.plot(epoch_num,training_acc)
plt.show()

#classification report


from sklearn.metrics import confusion_matrix, classification_report
y_pred = []
y_true = []

# Move the model to the device (GPU if available, CPU otherwise)
device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
model.to(device)

for images, labels in test_loader:
  # Move the images to the same device as the model
  images = images.to(device)

  predicted_output = model(images)

  _,predicted = torch.max(predicted_output,1)
  y_pred.extend(predicted.data.cpu().numpy())

  labels = labels.data.cpu().numpy()
  y_true.extend(labels)

cf_matrix = confusion_matrix(y_true, y_pred)
print(cf_matrix)
print(classification_report(y_true, y_pred))

torch.save(model.state_dict(), 'vehicle_cnn1.pt')

