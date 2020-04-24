from collections import OrderedDict

#Usage:
#from bismuthsimpleasset import BismuthSimpleAsset
#from bismuthclient import bismuthclient
#
#def asset_validity_function(asset_id):
#    return 1
#
#servers=["wallet2.bismuth.online:8150"]
#bismuth_client = bismuthclient.BismuthClient(verbose=False, servers_list=servers)
#
#register = "dragg:register"
#unregister = "dragg:unregister"
#address = "9ba0f8ca03439a8b4222b256a5f56f4f563f6d83755f525992fa5daf"
#thresholds = {"reg": 0} # Price to register, for spam filtering
#checkfunc = {"f": asset_validity_function} #Must be supplied by user
#assethandler = BismuthSimpleAsset(bismuth_client,address,register,
#                                  unregister,thresholds,checkfunc)
#
#out1 = assethandler.get_all_asset_ids()
#N = out1["total"]
#if N>0:
#    print("All registered asset ids={}".format(out1))
#    for i in range(0,N):
#        asset_id = out1["asset_id"][str(i)]
#        address = assethandler.get_registrant(asset_id)
#        print("Current registrant of {} = {}".format(asset_id,address))
#else:
#    print("There are no '{}' transactions with Bismuth recipient '{}'".format(register,address))
    
class BismuthSimpleAsset():

    def __init__(self,bismuth,address,reg,unreg,thresholds,checkfunc):
        self.bismuth = bismuth
        self.SERVICE_ADDRESS = address
        self.register = reg
        self.unregister = unreg
        self.thresholds = thresholds #Amount required to register
        self.checkfunc = checkfunc   #User-supplied function to check for valid ids

    def get_registrant(self,asset_id):
        """
        Returns the current registrant of a specified asset id
        """
        regs = self.__get_reg_unreg_sorted(asset_id)
        registrant = self.__get_registrant_from_regs(regs)
        return registrant

    def get_all_asset_ids(self):
        """
        Returns a dict with all valid asset ids submitted to the SERVICE_ADDRESS.
        An asset id can be associated with multiple accounts, if registered and
        unregistered multiple times.
        """
        data = {}
        command = "addlistop"
        to = self.SERVICE_ADDRESS
        op = self.register
        t_start = 0
        t_end = 9e10
        bismuth_params = [to,op,self.thresholds["reg"],False,False,t_start,t_end]
        bisdata = self.bismuth.command(command, bismuth_params)
        j = 0
        for i in range(0,len(bisdata)):
            data[j] = {}
            data[j]["asset_id"] = bisdata[i][11]
            data[j]["from"] = bisdata[i][2]
            data[j]["timestamp"] = bisdata[i][1]
            data[j]["type"] = "reg"
            j = j + 1

        op = self.unregister
        bismuth_params = [to,op,0,False,False,t_start,t_end]
        bisdata = self.bismuth.command(command, bismuth_params)
        for i in range(0,len(bisdata)):
            data[j] = {}
            data[j]["asset_id"] = bisdata[i][11]
            data[j]["from"] = bisdata[i][2]
            data[j]["timestamp"] = bisdata[i][1]
            data[j]["type"] = "unreg"
            j = j + 1

        out = self.__get_reg_unreg_all_sorted(data)
        out = self.__get_all_valid_asset_ids(out)
        return out

    def __get_all_valid_asset_ids(self,regs):
        """
        Returns a dict with all valid asset ids and associated addresses in input dict regs
        """
        out = {}
        asset_ids = {}
        j = 0
        for item in regs:
            asset_id = item[1]["asset_id"]
            check = self.checkfunc["f"](asset_id) #Checks if valid asset_id
            if check == 1:
                if item[1]['type'] == "reg":
                    try:
                        N = len(out[asset_id]["address"])
                        if len(out[asset_id]["address"][N-1]) == 0:
                            out[asset_id]["address"][N-1] = item[1]["from"]
                    except:
                        out[asset_id] = {}
                        out[asset_id]["address"] = []
                        out[asset_id]["address"].append(item[1]["from"])
                        asset_ids[str(j)] = asset_id
                        j = j + 1
                elif item[1]['type'] == "unreg":
                    try:
                        N = len(out[asset_id]["address"])
                        if out[asset_id]["address"][N-1] == item[1]["from"]:
                            out[asset_id]["address"].append("")
                    except:
                        pass

        # Remove duplicates and keep order
        for i in range(0,j):
            asset_id = asset_ids[str(i)]
            addr = out[asset_id]["address"]
            out[asset_id]["address"] = list(OrderedDict.fromkeys(addr))

        out["asset_id"] = asset_ids
        out["total"] = j
        return out

    def __get_reg_unreg_all_sorted(self,data):
        """
        Returns a dict of reg and unreg data, sorted by timestamp, multiple asset_id numbers
        It is assumed that the input data dict contains the following fields:
            timestamp, from, asset_id, type
        where from is the sender address and type is "reg" or "unreg"
        """
        regs = {}
        for i in range(0,len(data)):
            regs[data[i]['timestamp']]={'from': data[i]['from'], 'asset_id': data[i]['asset_id'], 'type': data[i]['type']}

        out = sorted(regs.items(), key=lambda x: x[0])
        return out

    def __get_reg_unreg_sorted(self,asset_id):
        """
        Returns a dict of reg and unreg data, sorted by timestamp, for a single asset_id
        """
        regs = {}
        command = "listexactopdata"
        bismuth_params = [self.register, asset_id]
        data = self.bismuth.command(command, bismuth_params)
        for i in range(0,len(data)):
            regs[data[i][1]]={'from': data[i][2], 'type': 'reg'}

        bismuth_params = [self.unregister, asset_id]
        data = self.bismuth.command(command, bismuth_params)
        for i in range(0,len(data)):
            regs[data[i][1]]={'from': data[i][2], 'type': 'unreg'}

        out = sorted(regs.items(), key=lambda x: x[0])
        return out

    def __get_registrant_from_regs(self,regs):
        """
        Returns the current registrant in the input dict regs.
        Handles multiple register and unregister events.
        """
        registrant = ""
        for item in regs:
            if item[1]['type'] == "reg":
                if len(registrant) == 0:
                    registrant = item[1]['from']
            elif item[1]['type'] == "unreg":
                if item[1]['from'] == registrant:
                    registrant = ""

        return registrant
