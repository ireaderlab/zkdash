// 将form转为AJAX提交
function ajaxSubmit(frm, fn) {
    var dataPara = getFormJson(frm);
    // alert(frm.action)
    var real_action = frm.action;
    if (frm.action.lastIndexOf('/index') > -1) {
        real_action = frm.action.replace('/index', '/search');
    }
    // alert(dumpProps(dataPara, 'dataPara'))
    $.ajax({
        url: real_action,
        type: frm.method,
        data: dataPara,
        success: fn,
        dataType: 'text',
    });
}

// 将form中的值转换为键值对。
function getFormJson(frm) {
    var json = {};
    var arr = $(frm).serializeArray();
    $.each(arr, function () {
        if (json[this.name] !== undefined) {
            if (!json[this.name].push) {
                json[this.name] = [json[this.name]];
            }
            json[this.name].push(this.value || '');
        } else {
            json[this.name] = this.value || '';
        }
    });

    return json;
}

// 调试js打印对象属性
function dumpProps(obj, obj_name) {
  var result = "";
  for (var i in obj) {
    result += obj_name + "." + i + " = " + obj[i] + "\n";
  }
  return result;
}
