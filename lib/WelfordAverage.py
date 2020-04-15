#https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance

#Do the average in a single pass!

class welford_average:
    def __init__(self, logger, count=0, mean=0,M2=0):
        self.logger = logger
        self.count = count
        self.mean = mean
        self.M2 = M2
        print(self.count, self.mean, self.M2)

    def update(self, new_value):
        self.count += 1 #increment N counter
        delta = new_value - self.mean
        self.mean += (delta/self.count)
        delta2 = new_value - self.mean
        self.M2 += ( delta * delta2)
        print(new_value , self.count, self.mean, self.M2)

    # Retrieve the mean, variance and sample variance from an aggregate
    def averages(self):
        print(self.count, self.mean, self.M2)
        if (self.count < 2):
            return float('nan')
        else:
            variance = self.M2/self.count
            sampleVariance = self.M2 / (self.count -1)
            return (self.count, self.mean , variance, sampleVariance)



test = welford_average(logger=None)
for i in range(1,10):
    #print(i)
    test.update(i)

print(test.averages())

