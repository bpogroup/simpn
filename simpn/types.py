class pn_list(tuple):
    def append(self, item):
        return pn_list(self + (item,))

    def delete(self, index):
        return pn_list(self[:index] + self[index+1:])
