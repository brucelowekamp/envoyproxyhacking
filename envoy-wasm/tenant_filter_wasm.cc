// NOLINT(namespace-envoy)
#include <string>
#include <string_view>
#include <unordered_map>
#include <functional>

#include "proxy_wasm_intrinsics.h"

class TenantRootContext : public RootContext {
public:
  explicit TenantRootContext(uint32_t id, std::string_view root_id) : RootContext(id, root_id) {}

  bool onStart(size_t) override;
  bool onConfigure(size_t) override;
  void onTick() override;

  // number of portions to split tenant into (0 for none)
  int tenantSplit(const std::string& tenant);
private:
  std::unordered_map<std::string, int> tenant_map;
};

class TenantContext : public Context {
public:
  explicit TenantContext(uint32_t id, RootContext* root) : Context(id, root) { parent = (TenantRootContext*) root; }

  //void onCreate() override;
  FilterHeadersStatus onRequestHeaders(uint32_t headers, bool end_of_stream) override;
  //FilterDataStatus onRequestBody(size_t body_buffer_length, bool end_of_stream) override;
  //FilterHeadersStatus onResponseHeaders(uint32_t headers, bool end_of_stream) override;
  //FilterDataStatus onResponseBody(size_t body_buffer_length, bool end_of_stream) override;
  //void onDone() override;
  //void onLog() override;
  //void onDelete() override;
private:
  std::hash<std::string> str_hash;
  TenantRootContext* parent;
    
};
static RegisterContextFactory register_TenantContext(CONTEXT_FACTORY(TenantContext),
                                                     ROOT_FACTORY(TenantRootContext),
                                                     "tenant_root_id");

bool TenantRootContext::onStart(size_t) {
  LOG_TRACE("onStart");
  return true;
}

bool TenantRootContext::onConfigure(size_t) {
  LOG_WARN("onConfigure");
  proxy_set_tick_period_milliseconds(1000); // 1 sec

  tenant_map.insert(std::make_pair<std::string,int>("megacorp", 10));
  tenant_map.insert(std::make_pair<std::string,int>("mediumcorp", 5));

  return true;
}

void TenantRootContext::onTick() {
  // place to load tenant configuration dynamically
  LOG_TRACE("onTick");
}

int TenantRootContext::tenantSplit(const std::string& tenant){
  auto entry = tenant_map.find(tenant);
  if (entry == tenant_map.end()) {
    return 0;
  }
  return entry->second;
}
  

FilterHeadersStatus TenantContext::onRequestHeaders(uint32_t, bool) {
  auto tenant = getRequestHeader("x-tenant")->toString();
  auto user = getRequestHeader("x-user")->toString();
  LOG_DEBUG(tenant + std::string(" - ") + user);

  auto split = parent->tenantSplit(tenant);
  if (split > 0) {
    std::string newkey = tenant + std::string("-") + std::to_string(str_hash(user)%split);
    LOG_INFO(newkey);
    replaceRequestHeader("X-key", newkey);
  }
  
  return FilterHeadersStatus::Continue;
}

