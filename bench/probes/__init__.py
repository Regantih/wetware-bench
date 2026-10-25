from . import (memory_capacity, narma, io_bandwidth, plasticity,
               learning_speed, stability, energy, criticality)

PROBES = {
    m.NAME: m
    for m in (memory_capacity, narma, io_bandwidth, plasticity,
              learning_speed, stability, energy, criticality)
}
