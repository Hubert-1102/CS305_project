# CS305_project

**目前进度**

proxy实现了对单个端口的代理，未实现通过DNS选择最优端口

已实现对 .f4m 文件的解析以获得视频支持的码率

已实现视频码率自动选择，但发现计算出的吞吐量远远大于视频码率，导致视频一直会选择最高码率播放，可能是计算方式有问题

已加入日志功能

已加入多线程，能在播放完视频后正常关闭代理

实现dns_server 与 netsim.py 的通信，获取运行netsim.py时的参数，即需要读取的文件

修改index.html文件以解决浏览器莫名其妙请求favicon.ico导致无法正常播放视频的问题

proxy以及dns_server必须也在容器中运行，否则外部(dns_server)无法通过socket与netsim.py通信
