/*** *** *** *** *** *** *** *** *** *** ***
 * QT4i-Instruments端-JavaScript引导程序
 *** *** *** *** *** *** *** *** *** *** ***/
/*
#import "_environment.js";
#import "_lib.js";
#import "_api.js";
*/
// -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
(function($) {
    Bootstrap = function() {
        $.log("--- --- --- --- --- ---");
        $.log('Bootstrap.Construction - Start');
        UIATarget['localTarget']()['setTimeout'](1);
        for (var i = 0; i < 15; i++) {
            var length = UIATarget['localTarget']()['frontMostApp']()['elements']().length;
            $.log('Bootstrap.Construction - app.elements: ' + length);
            if (length > 0) {
                break;
            };
            UIATarget['localTarget']()['delay'](0.5);
        };
        this.keep_running = true;
        $.log('Bootstrap.Construction - End');
    };
    Bootstrap.prototype = {
        get_json_result_struct : function(id, result, error) {
            var res_json = null;
            if (typeof result === 'boolean' && result == false) {
                res_json = false;
            } else{
                res_json = result ? result : null;
            };
            return {
                'id' : id,
                'result' : res_json,
                'error' : error ? error : null
            };
        },
        release : function() {
            this.keep_running = false;
            return 'released';
        },
        exec : function(command_json_string) {
            var command = eval('(' + command_json_string + ')'), result = null, error = null;
            if (command['method'] == 'release') {
                return this.get_json_result_struct(command['id'], this.release(), null);
            };
            try {
                command['params'].unshift(command['id']);
                result = api[command['method']].apply(null, command['params']);
            } catch(e) {
                error = e.message;
            };
            return this.get_json_result_struct(command['id'], result, error);
        },
        send_result : function(result) {
            var result = $.str.objectToString(result);
            var task = UIATarget['localTarget']()['host']()['performTaskWithPathArgumentsTimeout'](Environment['python_path'], [Environment['cmd_fetch_delegate'], '-xmlrpc_uri', Environment['xmlrpc_uri'], '-rpc_method', 'send_result', '-device_udid', Environment['device_udid'], '-result', result, '-timeout', String(Environment['cmd_fetch_delegate_timeout'])], Environment['cmd_fetch_delegate_timeout'] + 3);
            var exit_code = task['exitCode'];
            var stdout = task['stdout'];
            var stderr = task['stderr'];
            if (exit_code != 0) {
                $.log("--- --- --- --- --- ---");
                $.log("cmd_fetch_delegate - send_result - exit_code : " + exit_code);
                $.log("cmd_fetch_delegate - send_result - stdout    : " + stdout);
                $.log("cmd_fetch_delegate - send_result - stderr    : " + stderr);
                $.log("--- --- --- --- --- ---");
                api['uia.target.capture_screen']('cmd_fetch_delegate_error');
            };
        },
        send_result_and_get_next : function(result) {
            try {
                var result = $.str.objectToString(result);
                var task = UIATarget['localTarget']()['host']()['performTaskWithPathArgumentsTimeout'](Environment['python_path'], [Environment['cmd_fetch_delegate'], '-xmlrpc_uri', Environment['xmlrpc_uri'], '-rpc_method', 'send_result_and_get_next', '-device_udid', Environment['device_udid'], '-result', result, '-timeout', String(Environment['cmd_fetch_delegate_timeout'])], Environment['cmd_fetch_delegate_timeout'] + 3);
                var exit_code = task['exitCode'];
                var stdout = task['stdout'];
                var stderr = task['stderr'];
                if (exit_code == 0) {
                    return stdout && stdout != '' ? stdout : null;
                } else {
                    $.log("--- --- --- --- --- ---");
                    $.log("cmd_fetch_delegate - send_result_and_get_next - exit_code : " + exit_code);
                    $.log("cmd_fetch_delegate - send_result_and_get_next - stdout    : " + stdout);
                    $.log("cmd_fetch_delegate - send_result_and_get_next - stderr    : " + stderr);
                    $.log("--- --- --- --- --- ---");
                    api['uia.target.capture_screen']('cmd_fetch_delegate_error');
                };
            } catch(e) {
                if (e.identifier != 'UIAHostTaskTimeoutException') {
                    throw e;
                };
            };
        },
        start : function() {
            $.log("--- --- --- --- --- ---");
            $.log('Bootstrap.Start');
            $.log("--- --- --- --- --- ---");
            var timeout = Environment['timeout'] * 1000;
            var last_runtime = new Date().getTime();
            var result = this.get_json_result_struct(null, 'BootstrapStandBy', null);
            $.log('Server <<< ' + $.str.objectToString(result));
            while (this.keep_running) {
                var task_begin_time = new Date().getTime();
                var command = this.send_result_and_get_next(result);
                var task_duration = new Date().getTime() - task_begin_time;
                if (command) {
                    $.log("--- --- --- --- --- ---");
                    $.log('Server >>> ' + command);
                    $.log('TaskDuration    : ' + task_duration + '(millisecond)');
                    var command_begin_time = new Date().getTime();
                    result = this.exec(command);
                    if (!result.error && result.result == api.DoNotReturn) {
                        result = this.get_json_result_struct(null, null, null);
                    };
                    var command_duration = new Date().getTime() - command_begin_time;
                    $.log('CommandDuration : ' + command_duration + '(millisecond)');
                    $.log('Server <<< ' + $.str.objectToString(result));
                    if (Environment.ignore_cmd_error == false && result && result.error != null) {
                        this.send_result(result);
                        this.release();
                    };
                    last_runtime = new Date().getTime();
                } else {
                    if (new Date().getTime() - last_runtime > timeout) {
                        $.log('BootstrapTimeout');
                        this.release();
                    };
                };
            };
            $.log("--- --- --- --- --- ---");
            $.log('Bootstrap.Release');
            $.log("--- --- --- --- --- ---");
        }
    };
})($);
// -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
var bootstrap = new Bootstrap();
bootstrap.start();
// -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
