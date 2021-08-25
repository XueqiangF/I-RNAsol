#!/Users/11834/.conda/envs/Pytorch_GPU/python.exe
# -*- coding: UTF-8 -*-
'''=================================================
@Project -> File    ：RNASolventAccessibility -> feature_generate
@IDE    ：PyCharm
@Date   ：2021/5/9 15:55
=================================================='''
import os
import numpy as np
from configparser import ConfigParser
from processing_msa_to_psfm import Processing_MSA_To_PSFM, Processing_Aln_To_PSFM
import warnings
warnings.filterwarnings('ignore')
config = ConfigParser()
config.read('I-RNAsol.config')

Infernal = config.get('Infernal', 'Infernal')
cmsearch_DB = config.get('Infernal', 'cmsearch_DB')
RNAfold_EXE = config.get('RNAfold', 'RNAfold_EXE')
LinearPartition_EXE = config.get('LinearPartition', 'LinearPartition_EXE')

cmbuild_EXE = Infernal+"/cmbuild"
cmcalibrate_EXE = Infernal+"/cmcalibrate"
cmsearch_EXE = Infernal+"/cmsearch"

class FeaturesGeneration(object):
    def __init__(self, nucle_name: str, sequence: str, result_path: str):
        seq_path = os.path.join(result_path, nucle_name + ".fasta")
        with open(seq_path, "w") as f:
            f.write(">" + nucle_name.strip() + "\n" + sequence.strip())
        self.seq_path = seq_path
        self.nucle_name = nucle_name.strip()
        self.seq = sequence.strip()
        self.result_path = result_path
        self.onehot_path = os.path.join(self.result_path, self.nucle_name)
        self.LinearParitition_primary_SS_path = os.path.join(self.result_path, self.nucle_name + ".primary")
        self.LinearParitition_SS_path = os.path.join(self.result_path, self.nucle_name + ".ss")
        self.RNAfold_SS_path = os.path.join(self.result_path, self.nucle_name + ".fold")
        self.CM_path = os.path.join(self.result_path, self.nucle_name + ".cm")
        self.stockhom_path = os.path.join(self.result_path, self.nucle_name + ".sto")
        self.msa_path = os.path.join(self.result_path, self.nucle_name + ".msa")
        self.aln_path = os.path.join(self.result_path, self.nucle_name + ".aln")
        self.PSFM_path = os.path.join(self.result_path, self.nucle_name + ".psfm")

    def One_Hot_Encoding(self):
        one_hot_code = {"A": [1, 0, 0, 0],
                        "C": [0, 1, 0, 0],
                        "G": [0, 0, 1, 0],
                        "U": [0, 0, 0, 1]}
        with open(self.seq_path, "r") as seq: seq = seq.readlines()[1].strip()
        nucle_length = len(seq)
        OneHotVector = np.zeros((nucle_length, 4))
        for i in range(nucle_length):
            OneHotVector[i, :] = np.array(one_hot_code[seq[i]], float)
        np.savetxt(self.onehot_path, OneHotVector,fmt='%.00f')
        print(self.nucle_name + " One Hot Encoding is complete !!!")
        return OneHotVector

    def LinearParitition_SS(self):
        '''  RNA SS base-pairing probabilities generation by LinearPartition  '''
        if os.path.exists(self.LinearParitition_primary_SS_path):
            pass
        else:
            LinearPartition_cmd = "cat " + self.seq_path + " | " + LinearPartition_EXE + " -V " + "-r " + self.LinearParitition_primary_SS_path
            os.system(LinearPartition_cmd)
            print(self.nucle_name + " base-pairing probabilities generated by LinearPartition is complete !!!")
            with open(self.seq_path, "r") as fr:
                fr = fr.readlines()[1].strip()
            nucle_length = len(fr)
            ss_info = np.genfromtxt(self.LinearParitition_primary_SS_path, skip_header=1, dtype=float)
            prob_matr = np.zeros((nucle_length, 1))
            for i in range(1, nucle_length + 1):
                prob = np.array([], dtype=float)
                for j in range(ss_info.shape[0]):
                    if ss_info[j, 0] == i or ss_info[j, 1] == i:
                        prob = np.append(prob, ss_info[j, 2])
                if prob.shape[0] != 0:
                    max_prob = np.max(prob)
                    prob_matr[i - 1] = max_prob
                else:
                     prob_matr[i - 1] = 0.0
                del prob
            np.savetxt(self.LinearParitition_SS_path, prob_matr, fmt="%.3f")
            print(self.nucle_name + " Processing primary SS file is complete !!!")

    def RNAfold(self):
        if os.path.exists(self.RNAfold_SS_path):
            pass
        else:
            RNAfold_SS_cmd = RNAfold_EXE + " " + self.seq_path + ' --o '
            os.system(RNAfold_SS_cmd)
            CP_cmd = "cp -r ./" + self.nucle_name+".fold "+self.result_path
            os.system(CP_cmd)

    def BuiltStochlmFormat(self):
        if os.path.exists(self.RNAfold_SS_path):
            pass
        else:
            self.RNAfold()
            with open(self.RNAfold_SS_path, "r") as fr:
                fr = fr.readlines()
            with open(self.stockhom_path, "w") as fw:
                fw.write("# STOCKHOLM 1.0\n\n")
                seq_line = f"{fr[0].strip().replace('>', ''):18} {fr[1].strip()}"
                ss_line = f"{'#=GC SS_cons':18} {fr[2].strip().split(' ')[0]}"
                fw.write(seq_line + "\n")
                fw.write(ss_line + "\n" + "//")

    def msa_generation(self):
        if os.path.exists(self.aln_path):
            pass
        elif os.path.exists(self.stockhom_path):
            cmbuild_cmd = cmbuild_EXE + " " + self.CM_path + " " + self.stockhom_path
            os.system(cmbuild_cmd)
            print(self.nucle_name + " cmbuild is complete !!!")
            cmcalibrate_cmd = cmcalibrate_EXE + " " + self.CM_path
            os.system(cmcalibrate_cmd)
            print(self.nucle_name + " cmcalibrate is complete !!!")
            cmsearch_cmd = cmsearch_EXE + " -o " + self.msa_path + " " + self.CM_path + " " + cmsearch_DB
            os.system(cmsearch_cmd)
            print(self.nucle_name + " cmsearch is complete !!!")
        else:
            self.BuiltStochlmFormat()
            cmbuild_cmd = cmbuild_EXE + " " + self.CM_path + " " + self.stockhom_path
            os.system(cmbuild_cmd)
            print(self.nucle_name + " cmbuild is complete !!!")
            cmcalibrate_cmd = cmcalibrate_EXE + " " + self.CM_path
            os.system(cmcalibrate_cmd)
            print(self.nucle_name + " cmcalibrate is complete !!!")
            cmsearch_cmd = cmsearch_EXE + " -o " + self.msa_path + " " + self.CM_path + " " + cmsearch_DB
            os.system(cmsearch_cmd)
            print(self.nucle_name + " cmsearch is complete !!!")

    def PSFM_generation(self):
        if os.path.exists(self.PSFM_path):
            print("PSFM have existed!")
        elif os.path.exists(self.aln_path):
            print("Aln have existed!")
            MSAToPSFM = Processing_Aln_To_PSFM(self.aln_path)
            PSFM = MSAToPSFM.transform_numeric_MSA_to_PSFM()
            np.savetxt(self.PSFM_path, PSFM, fmt='%.03f')
        else:
            self.msa_generation()
            MSAToPSFM = Processing_MSA_To_PSFM(self.seq_path, self.msa_path, self.aln_path)
            PSFM = MSAToPSFM.transform_numeric_MSA_to_PSFM()
            np.savetxt(self.PSFM_path, PSFM, fmt='%.03f')


# def main():
#     import argparse
#     parser = argparse.ArgumentParser(description="I-RNAsol Predict Protein Solvent Accessibility")
#     parser.add_argument("-n", "--nucleotide name", required=True, type=str, help="nucleotide name")
#     parser.add_argument("-s", "--sequence", required=True, type=str, help="AA sequence ")
#     parser.add_argument("-o", "--result path", required=True, type=str, help="save result path")
#     args = parser.parse_args()
#     features_generation = FeaturesGeneration(args.nucle_name, args.sequence, args.result_path)
#     features_generation.One_Hot_Encoding()
#     features_generation.LinearParitition_SS()
#     features_generation.PSFM_generation()
#
#
# if __name__ == '__main__':
#     main()
