def fetch_ssm(ssm, param_name, is_json=False):
    return ssm.get_param(param_name, param_type="json" if is_json else None)
