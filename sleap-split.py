#!/usr/bin/env python

# Import libraries
import glob
import os.path
import subprocess
import sys

import sleap
import seaborn as sns
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy

import pandas as pd

sleap.use_cpu_only()

# Define functions
def get_right_node_coords(predictions, instance):
    x_list = []
    for point in range(0,7):
        x_list.append(predictions[0][instance][:][point][0])
    max_x = numpy.nanmax(x_list)

    for point in range(0,7):
        if x_list[point] == max_x:
            max_point = point

    max_point_coords =  predictions[0][instance][:][max_point]
    return(max_point_coords)

def get_corner_nodes(point_coords, x_pad_left = 20, x_pad_right = 120, y_pad = 100):

    l_x_pos = point_coords[0] - x_pad_right
    l_y_pos = point_coords[1]
    r_x_pos = point_coords[0] 
    r_y_pos = point_coords[1]

    corner_nodes = {"point_left_a" : (l_x_pos - x_pad_left, l_y_pos + y_pad),
"point_left_b" : (l_x_pos - x_pad_left, l_y_pos - y_pad),
"point_right_a" : (r_x_pos + x_pad_left, r_y_pos + y_pad),
"point_right_b" : (r_x_pos + x_pad_left, r_y_pos - y_pad)}
    return(corner_nodes)

def plot_points(corner_nodes, predictions, instance):
    
    plt.plot(corner_nodes["point_left_a"][0], corner_nodes["point_left_a"][1], marker = "o")
    plt.plot(corner_nodes["point_left_b"][0], corner_nodes["point_left_b"][1], marker = "o")
    plt.plot(corner_nodes["point_right_a"][0], corner_nodes["point_right_a"][1], marker = "o")
    plt.plot(corner_nodes["point_right_b"][0], corner_nodes["point_right_b"][1], marker = "o")

    for point in range(0,7):
        plt.plot(predictions[0][instance][:][point][0], predictions[0][instance][:][point][1], marker = "o")
        plt.plot(predictions[0][instance][:][point][0], predictions[0][instance][:][point][1])

def get_left_points(predictions_filename, video_file):
    
    predictions = sleap.load_file(predictions_filename)
    max_point_coords_list = []
    
    for i in range(0,len(predictions[0])):
        max_point_coords_list.append(get_right_node_coords(predictions, i))
        
    corner_nodes_list = []
    for point in max_point_coords_list:
        corner_nodes_list.append(get_corner_nodes(point))
        
    left_points = []
    for d in corner_nodes_list:
        left_points.append(d['point_left_b'])
        
    pd.DataFrame(left_points).to_csv(predictions_filename+".left_point_coords.csv")
    
    video = sleap.load_video(video_file)
    imgs = video[0]
    
    plt.imshow(imgs[0])
    for x, y in left_points:
        plt.plot(x,y, marker = "o")
    plt.savefig(predictions_filename+".png")
    plt.close()

def split_videos(predictions_file, video_file, pad = 200):
    df = pd.read_csv(predictions_file)
    split_command_list = []
    
    for i in range(0,len(df)):
        x = round(df.iloc[i][1])
        
        y = round(df.iloc[i][2])
        
        out_file = video_file+".instance."+str(i)+".mp4"
        split_command_list.append(f"ffmpeg -y -i {video_file} -filter:v crop={pad}:{pad}:{x}:{y} -c:v libx264 -pix_fmt yuv420p -preset superfast -crf 23 {out_file}"
                                  )
    for split_command in split_command_list:
        subprocess.run([split_command], shell = True)

# Main

## Inputs
video_input = sys.argv[1]
input_pad = sys.argv[2]

script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))

model1=script_directory+"/models/230115_170427.centered_instance"
model2=script_directory+"/models/230115_170427.centroid"

## Mov to MP4
video_input_split = os.path.splitext(video_input)
video_input_split_extension = video_input_split[1]
mov = video_input_split_extension == ".mov"

if mov:
    print("Converting mov to mp4")
    video_input_mp4 = os.path.splitext(video_input)
    video_input_mp4 = video_input_mp4[0]+".mp4"

    command_mov2mp4 = f"ffmpeg -y -i {video_input} -c:v libx264 -pix_fmt yuv420p -preset superfast -crf 23 {video_input_mp4}"
    subprocess.run(command_mov2mp4, shell = True)
    
    video_input = video_input_mp4
    print("Converting mov to mp4: finished")

## Output names
predictions_output = video_input+".predictions.slp"
left_points_csv = predictions_output+".left_point_coords.csv"


## Predict chambers
print("Predict chambers")

command_predict_chambers = f'sleap-track --frames 999-1000 -m {model1} -m {model2} -o {predictions_output} {video_input}'
subprocess.run([command_predict_chambers], shell = True)

print("Predict chambers: finished")

## Get split coords
print("Get split coords")
get_left_points(predictions_output, video_input)
print("Get split coords: finished")

## Split videos
print("Split videos")
split_videos(left_points_csv, video_input, pad = input_pad)
print("Split videos: finished")
