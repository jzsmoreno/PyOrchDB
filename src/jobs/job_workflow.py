import argparse

# get regularization hyperparameter
parser = argparse.ArgumentParser()
parser.add_argument("--regularization", type=float, dest="reg_rate", default=0.01)
args = parser.parse_args()
try:
    reg = reg = args.reg_rate
except:
    pass

print("Hello World!")
