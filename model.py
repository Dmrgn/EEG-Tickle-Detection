# copy of model.ipynb but in a plain python file
import tensorflow as tf
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout, Input
from tensorflow.keras.models import Sequential
import numpy as np 


# Define the input shape
input_shape = (30, 31, 1)  # Grayscale images have a single channel
num_classes = 3
model = Sequential()

# First Convolutional Layer
model.add(Input(input_shape))
model.add(Conv2D(filters=32, kernel_size=(3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(3, 3)))
# Second Convolutional Layer
model.add(Conv2D(filters=64, kernel_size=(4, 4), activation='relu'))
model.add(MaxPooling2D(pool_size=(3, 3)))
# Flatten the 2D arrays for the fully connected layers
model.add(Flatten())
# Fully connected layer
model.add(Dense(units=128, activation='relu'))
# Dropout for regularization
model.add(Dropout(0.2))
# Fully connected layer
model.add(Dense(units=32, activation='relu'))
# Dropout for regularization
model.add(Dropout(0.2))
# Output layer
model.add(Dense(units=num_classes, activation='softmax'))

# Compile the model
model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

# Directory containing the dataset
data_dir = './dataset'

# Load the dataset
batch_size = 32
img_height = 31
img_width = 30

# Load training dataset
train_dataset = tf.keras.preprocessing.image_dataset_from_directory(
    data_dir,
    labels='inferred',
    label_mode='int',  # can be 'int' for integer labels or 'categorical' for one-hot encoded labels
    color_mode='grayscale',  # because the images are grayscale
    batch_size=batch_size,
    image_size=(img_height, img_width),  # resize the images
    shuffle=True,
    seed=42,
    validation_split=0.2,
    subset='training',
)

# Load validation dataset
validation_dataset = tf.keras.preprocessing.image_dataset_from_directory(
    data_dir,
    labels='inferred',
    label_mode='int',
    color_mode='grayscale',
    batch_size=batch_size,
    image_size=(img_height, img_width),
    shuffle=True,
    seed=42,
    validation_split=0.2,
    subset='validation',
)

def normalize(image, label):
    image = tf.cast(image, tf.float32) / 255.0
    return image, label

train_dataset = train_dataset.map(normalize)
validation_dataset = validation_dataset.map(normalize)
train_dataset = train_dataset.repeat(10)
validation_dataset = validation_dataset.repeat(10)

model.fit(
    train_dataset,
    validation_data=validation_dataset,
    epochs=10
)

model.save('./model.h5')