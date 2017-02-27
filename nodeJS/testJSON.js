var str = { channel: 'b4da8ed9739192268ba5667b4d10545b09e45d83|light_bulb-1702387|user-331666',
  subscription: null,
    actualChannel: null,
      subscribedChannel: 'b4da8ed9739192268ba5667b4d10545b09e45d83|light_bulb-1702387|user-331666',
        timetoken: '14881566572979594',
          publisher: 'c125c661-2ff7-43ad-af63-f499a93c0d0d',
            message: '{"capabilities":{},"created_at":1463365454,"desired_state":{},"device_manufacturer":"lutron","gang_id":null,"hidden_at":null,"hub_id":"238470","icon_code":"light_bulb-light_bulb","icon_id":"71","last_reading":{"brightness":1.0,"brightness_changed_at":1488150711.733138,"brightness_updated_at":1488156656.8756323,"connection":true,"connection_updated_at":1488156656.8756323,"desired_brightness_changed_at":1488147256.6411865,"desired_brightness_updated_at":1488150993.7392445,"desired_powered_changed_at":1488150833.9922142,"desired_powered_updated_at":1488150833.9922142,"needs_repair":false,"needs_repair_updated_at":1488156656.8756323,"powered":true,"powered_changed_at":1488156656.8756323,"powered_updated_at":1488156656.8756323},"lat_lng":[44.933013,-93.457665],"light_bulb_id":"1702387","linked_service_id":null,"local_id":"8","locale":"en_us","location":"55345","manufacturer_device_id":null,"manufacturer_device_model":"lutron_p_pkg1_w_wh_d","model_name":"Caseta Wireless Dimmer \\u0026 Pico","name":"Master Chair Lamp","object_id":"1702387","object_type":"light_bulb","order":0,"radio_type":"lutron","subscription":{"pubnub":{"channel":"b4da8ed9739192268ba5667b4d10545b09e45d83|light_bulb-1702387|user-331666","subscribe_key":"sub-c-f7bf7f7e-0542-11e3-a5e8-02ee2ddab7fe"}},"triggers":[],"units":{},"upc_code":"lutron_p-pkg1w-wh-d","upc_id":"556","user_ids":["331666"],"uuid":"4d5ff92e-abce-45d6-8fcf-e0e1f5a5ef39","nonce":0}' }
var obj = JSON.parse(str);

console.log(obj.name);
