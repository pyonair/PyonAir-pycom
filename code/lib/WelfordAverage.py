  
#https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance

#Do the average in a single pass!

class WelfordAverage:
    def __init__(self, logger, count=0, mean=0,M2=0):

        self.logger = logger
        self.logger.debug("New welford averager...")
        self.welfordsCount = count
        self.welfordsMean = mean
        self.welfordsM2 = M2
        #print(self.count, self.mean, self.M2)

    def reset(self):
        self.count = 0
        self.mean = 0
        self.M2 = 0
        

    def update(self, new_value):
        self.count += 1 #increment N counter
        delta = new_value - self.mean
        self.mean += (delta/self.count)
        delta2 = new_value - self.mean
        self.M2 += ( delta * delta2)
        #print(new_value , self.count, self.mean, self.M2)

    def getAverageAndReset(self):
        count, mean , variance, sampleVariance = self.getAverage()
        self.reset()
        return (count, mean , variance, sampleVariance)

    # Retrieve the mean, variance and sample variance from an aggregate
    def getAverage(self):
        #self.logger.debug("{} {} {} ".format(self.count, self.mean, self.M2))
        if (self.count < 2):
            return float('nan')
        else:
            variance = self.M2/self.count
            sampleVariance = self.M2 / (self.count -1)
            return (self.count, self.mean , variance, sampleVariance)

