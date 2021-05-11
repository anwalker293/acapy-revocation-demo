from typing import Any, Dict, List, Type, TypeVar, Union

import attr

from ..models.indy_proof_req_non_revoked import IndyProofReqNonRevoked
from ..models.indy_proof_request_requested_attributes import IndyProofRequestRequestedAttributes
from ..models.indy_proof_request_requested_predicates import IndyProofRequestRequestedPredicates
from ..types import UNSET, Unset

T = TypeVar("T", bound="IndyProofRequest")


@attr.s(auto_attribs=True)
class IndyProofRequest:
    """ """

    requested_attributes: IndyProofRequestRequestedAttributes
    requested_predicates: IndyProofRequestRequestedPredicates
    name: Union[Unset, str] = UNSET
    non_revoked: Union[Unset, IndyProofReqNonRevoked] = UNSET
    nonce: Union[Unset, str] = UNSET
    version: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        requested_attributes = self.requested_attributes.to_dict()

        requested_predicates = self.requested_predicates.to_dict()

        name = self.name
        non_revoked: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.non_revoked, Unset):
            non_revoked = self.non_revoked.to_dict()

        nonce = self.nonce
        version = self.version

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "requested_attributes": requested_attributes,
                "requested_predicates": requested_predicates,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if non_revoked is not UNSET:
            field_dict["non_revoked"] = non_revoked
        if nonce is not UNSET:
            field_dict["nonce"] = nonce
        if version is not UNSET:
            field_dict["version"] = version

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        requested_attributes = IndyProofRequestRequestedAttributes.from_dict(d.pop("requested_attributes"))

        requested_predicates = IndyProofRequestRequestedPredicates.from_dict(d.pop("requested_predicates"))

        name = d.pop("name", UNSET)

        non_revoked: Union[Unset, IndyProofReqNonRevoked] = UNSET
        _non_revoked = d.pop("non_revoked", UNSET)
        if not isinstance(_non_revoked, Unset):
            non_revoked = IndyProofReqNonRevoked.from_dict(_non_revoked)

        nonce = d.pop("nonce", UNSET)

        version = d.pop("version", UNSET)

        indy_proof_request = cls(
            requested_attributes=requested_attributes,
            requested_predicates=requested_predicates,
            name=name,
            non_revoked=non_revoked,
            nonce=nonce,
            version=version,
        )

        indy_proof_request.additional_properties = d
        return indy_proof_request

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
