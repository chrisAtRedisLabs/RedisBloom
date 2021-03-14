# RedisBloom T-Digest Documentation

## Create / Reset

### TDIGEST.CREATE

Allocate the memory and initialize the t-digest.

```
TDIGEST.CREATE {key} {compression}
```

#### Parameters:

* **key**: The name of the sketch.
* **compression**: The compression parameter. 100 is a common value for normal uses. 1000 is extremely large.
    
#### Complexity

O(1)

#### Return

OK on success, error otherwise

#### Example

```
TDIGEST.CREATE t-digest 100
```

### TDIGEST.RESET

Reset a histogram to zero - empty out a histogram and re-initialize it.

```
TDIGEST.RESET {key}
```

#### Parameters:

* **key**: The name of the sketch.
    
#### Complexity

O(1)

#### Return

OK on success, error otherwise

#### Example

```
TDIGEST.RESET t-digest
```


## Update

### TDIGEST.ADD

Adds one or more samples to a histogram.

```
TDIGEST.ADD {key} {val} {weight} [ {val} {weight} ] ...
```

#### Parameters:

* **key**: The name of the sketch.
* **val**: The value to add.
* **weight**: The weight of this point.
    
#### Complexity

O(N) , where N is the number of samples to add

#### Return

OK on success, error otherwise

#### Example

```
TDIGEST.ADD key 1500.0 1.0
```


## Merge

### TDIGEST.MERGE

Merges all of the values from 'from' to 'this' histogram.

```
TDIGEST.MERGE {to-key} {from-key}
```

#### Parameters:

* **to-key**: Histogram to copy values to.
* **from-key**: Histogram to copy values from.

#### Complexity

O(N), where N is the number of centroids 

#### Return

OK on success, error otherwise

#### Example

```
TDIGEST.MERGE to-sketch from-sketch
```

## Query

### TDIGEST.MIN

Get minimum value from the histogram.  Will return __DBL_MAX__ if the histogram is empty.

```
TDIGEST.MIN {key}
```

#### Parameters:

* **key**: The name of the sketch.

#### Complexity

O(1)

#### Return

Minimum value from the histogram.  Will return __DBL_MAX__ if the histogram is empty.

#### Example 

```
1127.0.0.1:6379> TDIGEST.MIN key
"10"
```



### TDIGEST.MAX

Get maximum value from the histogram.  Will return __DBL_MIN__ if the histogram is empty.

```
TDIGEST.MAX {key}
```

#### Parameters:

* **key**: The name of the sketch.

#### Complexity

O(1)

#### Return

Maximum value from the histogram.  Will return __DBL_MIN__ if the histogram is empty.

#### Example 

```
1127.0.0.1:6379> TDIGEST.MAX key
"10000"
```


### TDIGEST.QUANTILE

Returns an estimate of the cutoff such that a specified fraction of the data
added to this TDigest would be less than or equal to the cutoff.

```
TDIGEST.QUANTILE {key} {quantile}
```

#### Parameters:

* **key**: The name of the sketch.
* **quantile**: The desired fraction ( between 0 and 1 inclusively ).
    
#### Complexity

O(1)

#### Return

Double value estimate of the cutoff such that a specified fraction of the data
added to this TDigest would be less than or equal to the cutoff.

#### Example

```
127.0.0.1:6379> TDIGEST.QUANTILE key 0.5
"100"
```

### TDIGEST.CDF

Returns the fraction of all points added which are <= value.

```
TDIGEST.CDF {key} {value}
```

#### Parameters:

* **key**: The name of the sketch.
* **quantile**: upper limit for which the fraction of all points added which are <= value.
    
#### Complexity

O(1)

#### Return

Double fraction of all points added which are <= value.

#### Example

```
127.0.0.1:6379> TDIGEST.CDF key 10
"0.041666666666666664"
```


## General

### TDIGEST.INFO

Returns compression, capacity, total merged and unmerged nodes, the total compressions 
made up to date on that key, and merged and unmerged weight.

```
TDIGEST.INFO {key}
```

### Parameters:

* **key**: The name of the sketch.

### Complexity

O(1) 

#### Example

```
127.0.0.1:6379> tdigest.info key
 1) Compression
 2) (integer) 100
 3) Capacity
 4) (integer) 610
 5) Merged nodes
 6) (integer) 3
 7) Unmerged nodes
 8) (integer) 2
 9) Merged weight
10) "120"
11) Unmerged weight
12) "1000"
13) Total compressions
14) (integer) 1
```
