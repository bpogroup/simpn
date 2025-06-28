from datetime import datetime, timedelta
from enum import Enum, auto


class TimeUnit(Enum):
    """An enumeration for the unit in which simulation time is measured."""
    SECONDS = auto()
    """
    Measured in seconds.
    
    :meta hide-value:
    """
    MINUTES = auto()
    """
    Measured in minutes.

    :meta hide-value:
    """
    HOURS = auto()
    """
    Measured in hours.

    :meta hide-value:
    """
    DAYS = auto()
    """
    Measured in days.

    :meta hide-value:
    """


class Reporter:
    """
    A reporter can be passed to the simpn.simulator.SimProblem.simulate function to report on what happens during the simulator.
    To this end, a reported must implement the callback function.
    """
    def callback(self, timed_binding):
        """
        A function that is invoked by a simpn.simulator.SimProblem each time a event happened.
        It receives a timed_binding, which is a triple (binding, time, event):
        - binding = [(v1: SimVar, t1: SimToken), (v2: SimVar, t2: SimToken), ...] of the variable values that caused the event.
        - time is the simulation time at which the event happened.
        - event: SimEvent is the event that happened.

        :param timed_binding: the triple (binding, time, event) that described the event that happened with its variable values and the time at which it happened.
        """
        raise NotImplementedError


class SimpleReporter(Reporter):
    """
    A simple reporter that just prints the occurring events to the standard output.
    """
    def callback(self, timed_binding):
        result = str(timed_binding[2]) + "{"
        i = 0
        for var, token in timed_binding[0]:
            result += str(var) + ": " + str(token.value)
            if i < len(timed_binding[0])-1:
                result += ", "
            i += 1
        result += "}" + "@t=" + str(timed_binding[1])
        print(result)


class WarmupReporter(Reporter):
    """
    A reporter that reports on the warmup period of a simulation by computing the average cycle times over time.
    It assumes tasks are executed for cases that arrive via start_events and complete at end_events.
    """
    def __init__(self):
        self.times = [0]
        self.average_cycle_times = [0]

        self.__total_times = [0]
        self.__nr_completed_cases = 0
        self.__case_arrivals = {}

    def callback(self, timed_binding):
        (binding, time, event) = timed_binding
        if event.get_id().endswith("<start_event>"):
            case_id = binding[0][1].value  # the case_id is always [0] the first variable in the binding, the [1] token value of that, and [0] the case_id of the value.
            self.__case_arrivals[case_id] = time
        elif event.get_id().endswith("<end_event>"):
            case_id = binding[0][1].value[0]  # the case_id is always [0] the first variable in the binding, the [1] token value of that, and [0] the case_id of the value.
            waiting_time = time - self.__case_arrivals[case_id]
            total_time = self.__total_times[self.__nr_completed_cases]
            total_time += waiting_time
            self.__nr_completed_cases += 1
            self.times.append(time)
            self.__total_times.append(total_time)
            self.average_cycle_times.append(total_time/self.__nr_completed_cases)


class ProcessReporter(Reporter):
    """
    A reporter that heavily depends on the process prototypes (task, start_event, intermediate_event, end_event) to report on what happens.
    It assumes tasks are executed for cases that arrive via start_events and complete at end_events. It measures:
    - nr_started: the number of cases that started.
    - nr_completed: the number of cases that completed.
    - total_wait_time: the sum of waiting times of completed cases.
    - total_proc_time: the sum of processing times of completed cases.
    - total_cycle_time: the sum of cycle times of completed cases.
    - resource_busy_times: a mapping of resource_id -> the time the resource was busy during simulation.
    """

    def __init__(self, warmup_time=0):
        self.resource_busy_times = dict()  # mapping of resource_id -> the time the resource was busy during simulation.
        self.nr_started = 0  # number of cases that started
        self.nr_completed = 0  # number of cases that completed
        self.total_wait_time = 0  # sum of waiting times of completed cases
        self.total_proc_time = 0  # sum of processing times of completed cases
        self.total_cycle_time = 0  # sum of cycle times of completed cases

        self.__status = dict()  # case_id -> (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change); time_last_busy_change is the time nr_busy_tasks last went from 0 to 1 or from 1 to 0
        self.__resource_start_times = dict()  # resource -> time
        self.__last_time = 0

        self.warmup_time = warmup_time

    def callback(self, timed_binding):
        (binding, time, event) = timed_binding
        self.__last_time = time
        if event.get_id().endswith("<start_event>"):
            case_id = binding[0][1].value  # the case_id is always [0] the first variable in the binding, the [1] token value of that, and [0] the case_id of the value.
            self.__status[case_id] = (0, time, 0, 0, time)
            if time > self.warmup_time:
                self.nr_started += 1
        elif event.get_id().endswith("<task:start>"):
            case_id = binding[0][1].value[0]  # the case_id is always [0] the first variable in the binding, the [1] token value of that, and [0] the case_id of the value.
            resource_id = binding[1][1].value  # the resource_id is always [1] the second variable in the binding, the [1] token value of that.
            self.__resource_start_times[resource_id] = time
            (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change) = self.__status[case_id]
            if nr_busy_tasks == 0:
                sum_wait_times += time - time_last_busy_change
                time_last_busy_change = time
            nr_busy_tasks += 1
            self.__status[case_id] = (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change)
        elif event.get_id().endswith("<task:complete>"):
            case_id = binding[0][1].value[0][0]  # the case_id is always [0] the first variable in the binding, the [1] token value of that, and [0] the case_id of the value.
            resource_id = binding[0][1].value[1]  # the resource_id is always [0] the first variable in the binding, the [1] token value of that, and [1] the resource_id of the value.
            if time > self.warmup_time:
                if resource_id not in self.resource_busy_times.keys():
                    self.resource_busy_times[resource_id] = 0
                if self.__resource_start_times[resource_id] < self.warmup_time:
                    self.resource_busy_times[resource_id] += time - self.warmup_time
                else:
                    self.resource_busy_times[resource_id] += time - self.__resource_start_times[resource_id]
            del self.__resource_start_times[resource_id]
            (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change) = self.__status[case_id]
            if nr_busy_tasks == 1:
                sum_proc_times += time - time_last_busy_change
                time_last_busy_change = time
            nr_busy_tasks -= 1
            self.__status[case_id] = (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change)
        elif event.get_id().endswith("<end_event>"):
            case_id = binding[0][1].value[0]  # the case_id is always [0] the first variable in the binding, the [1] token value of that, and [0] the case_id of the value.
            (nr_busy_tasks, arrival_time, sum_wait_times, sum_proc_times, time_last_busy_change) = self.__status[case_id]
            del self.__status[case_id]
            if arrival_time > self.warmup_time:
                self.nr_completed += 1
                self.total_wait_time += sum_wait_times
                self.total_proc_time += sum_proc_times
                self.total_cycle_time += time - arrival_time

    def print_result(self):
        print("Nr. cases started:            ", self.nr_started)
        print("Nr. cases completed:          ", self.nr_completed)
        print("Avg. waiting time per case:   ", round(self.total_wait_time/self.nr_completed, 3))
        print("Avg. processing time per case:", round(self.total_proc_time/self.nr_completed, 3))
        print("Avg. cycle time per case:     ", round(self.total_cycle_time/self.nr_completed, 3))

        # process the resources that are currently busy
        for resource_id in self.__resource_start_times.keys():
            self.resource_busy_times[resource_id] += self.__last_time - self.__resource_start_times[resource_id]

        self.__resource_start_times.clear()
        
        for resource_id in self.resource_busy_times.keys():
            print("Resource", resource_id, "utilization:", round(self.resource_busy_times[resource_id]/(self.__last_time - self.warmup_time), 2))

class EventLogReporter(Reporter):
    """
    A reporter that heavily depends on the process prototypes (task, start_event, intermediate_event, end_event) to report on what happens.
    It stores the events that happen in an event log that can be mined with some process mining tool.
    As simulation time is a numerical value, some processing is done to convert simulation time
    into a time format that can be read and interpreted by a process mining tool. To that end,
    the timeunit in which simulation time is measured must be passed as well as the
    initial_time moment in calendar time from which the simulation time will be measured.
    A particular simulation_time moment will then be stored in the log as:
    initial_time + simulation_time timeunits. Data can also be reported on by specifying the
    corresponding data fields. The log will contain these data fields as additional columns in the order specified.
    The case that is processed in each task is assumed to have the same number of data fields as the data_fields parameter.
    The data of each case must initially be generated by the start event and can be modified by tasks.
    Each task must pass the same data fields, optionally with modified values.

    :param filename: the name of the file in which the event log must be stored.
    :param timeunit: the :class:`.TimeUnit` of simulation time.
    :param initial_time: a datetime value.
    :param time_format: a datetime formatting string.
    :param data_fields: the data fields to report in the log.
    :param separator: the separator to use in the log.
    :param data_fields: a list of data field names to include in the log.
    """
    def __init__(self, filename, timeunit=TimeUnit.MINUTES, initial_time=datetime(2020, 1, 1), time_format="%Y-%m-%d %H:%M:%S.%f", separator=",", data_fields=None):
        self.task_start_times = dict()
        self.timeunit = timeunit
        self.initial_time = initial_time
        self.time_format = time_format
        self.logfile = open(filename, "wt")
        self.sep = separator        
        self.data_fields = data_fields
        self.logfile.write("case_id"+self.sep+"task"+self.sep+"resource"+self.sep+"start_time"+self.sep+"completion_time")
        if data_fields is not None:
            for field in data_fields:
                self.logfile.write(self.sep + field)
        self.logfile.write("\n")

    def displace(self, time):
        return self.initial_time + (timedelta(seconds=time) if self.timeunit == TimeUnit.SECONDS else timedelta(
            minutes=time) if self.timeunit == TimeUnit.MINUTES else timedelta(
            hours=time) if self.timeunit == TimeUnit.HOURS else timedelta(
            days=time) if self.timeunit == TimeUnit.DAYS else None)

    def callback(self, timed_binding):
        (binding, time, event) = timed_binding        
        if event.get_id().endswith("<task:start>"):            
            case_id = binding[0][1].value[0]
            task = event.get_id()[:event.get_id().index("<")]
            self.task_start_times[(case_id, task)] = time
        elif event.get_id().endswith("<task:complete>"):
            case_id = binding[0][1].value[0][0]
            task = event.get_id()[:event.get_id().index("<")]
            resource = binding[0][1].value[1]
            if (case_id, task) in self.task_start_times.keys():
                self.logfile.write(str(case_id) + self.sep)
                self.logfile.write(task + self.sep)
                self.logfile.write(str(resource) + self.sep)
                self.logfile.write(self.displace(self.task_start_times[(case_id, task)]).strftime(self.time_format) + self.sep)
                self.logfile.write(self.displace(time).strftime(self.time_format))
                if self.data_fields is not None:
                    data = binding[0][1].value[0][1:]
                    data_i = 0
                    for _ in self.data_fields:
                        self.logfile.write(self.sep)
                        if data_i < len(data):
                            self.logfile.write(str(data[data_i]))
                        data_i += 1
                self.logfile.write("\n")
                self.logfile.flush()
                del self.task_start_times[(case_id, task)]
        elif event.get_id().endswith("<start_event>") or event.get_id().endswith("<intermediate_event>") or event.get_id().endswith("<end_event>"):
            if event.get_id().endswith("<start_event>"):
                case_id = binding[0][1].value
            else:
                case_id = binding[0][1].value[0]
            event = event.get_id()[:event.get_id().index("<")]
            self.logfile.write(str(case_id) + self.sep)
            self.logfile.write(event + self.sep)
            self.logfile.write(self.sep)
            self.logfile.write(self.displace(time).strftime(self.time_format) + self.sep)
            self.logfile.write(self.displace(time).strftime(self.time_format))
            if self.data_fields is not None:
                for _ in self.data_fields:
                    self.logfile.write(self.sep)
            self.logfile.write("\n")
            self.logfile.flush()

    def close(self):
        self.logfile.close()