#!/bin/bash


function test() {
	./$1.act | diff $1.out -
	if [ $? -eq "1" ]; then
		echo "FAILED $1"
	fi
}

test "echo"
test "inflows"
test "vars"
