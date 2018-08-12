import sys


class Progress:
    total_stages = 0
    cur_stage = 0
    steps_on_this_stage = 0
    cur_step_on_this_stage = 0
    msg = ''

    def next_stage(self):
        if self.steps_on_this_stage != 0:
            self.update(self.steps_on_this_stage, self.steps_on_this_stage)
        sys.stdout.write('\n')
        sys.stdout.flush()
        self.cur_stage += 1

    def update(self, steps, total_steps):
        self.steps_on_this_stage = total_steps
        self.cur_step_on_this_stage = steps
        self._update()

    def step_msg(self, msg):
        self.msg = msg
        self._update()

    def clear_step_msg(self):
        self.step_msg('')

    def error(self, msg):
        sys.stdout.write('\r' + msg)
        self._update()

    def _update(self):
        percent = (float(self.cur_step_on_this_stage) / float(self.steps_on_this_stage)) * 100
        title = '%s of %s' % (self.cur_stage + 1, self.total_stages)
        steps_text = '(%s / %s)' % (self.cur_step_on_this_stage, self.steps_on_this_stage)
        msg_text = ' | ' + self.msg if self.msg else ''
        text = title.ljust(10) + ' [' + ('#' * int((5 * round(float(percent)) / 5) / 5)).ljust(20) + '] ' + steps_text + msg_text
        sys.stdout.write('\r' + text)
        sys.stdout.flush()
